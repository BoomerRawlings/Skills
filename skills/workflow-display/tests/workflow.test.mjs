import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import vm from 'node:vm';
import { validateData, readData } from '../scripts/validate.mjs';
import { buildWorkflow, renderWorkflow, serializeData } from '../scripts/build.mjs';

const directory = fileURLToPath(new URL('../', import.meta.url));
const builder = path.join(directory, 'scripts', 'build.mjs');
const validator = path.join(directory, 'scripts', 'validate.mjs');
const example = path.join(directory, 'examples', 'content-pipeline.json');
const fixture = () => ({
  title: 'A small workflow', description: 'Two real explanation/artifact pairs.',
  plans: [{id: 'first-plan', title: 'First plan', summary: 'Build from a clear input.', steps: [
    {id: 'brief', title: 'Define the input', description: 'Write one concrete question.', artifact: {title: 'Input record', code: 'Question: where should we begin?'}},
    {id: 'draft', title: 'Use the input', description: 'Answer the recorded question.', artifact: {title: 'Draft', language: 'text', code: 'Begin with the smallest useful task.'}, related: ['brief']},
  ]}],
});

async function temp(t) {
  const location = await mkdtemp(path.join(tmpdir(), 'workflow-display-test-'));
  t.after(() => rm(location, {recursive: true, force: true}));
  return location;
}

function embeddedData(html) {
  const match = html.match(/<script type="application\/json" id="workflow-data">([\s\S]*?)<\/script>/);
  assert.ok(match, 'generated page includes its data');
  return JSON.parse(match[1]);
}

test('bundled workflows validate and contain actual cross-step dependencies', async () => {
  for (const name of ['content-pipeline', 'research-review']) {
    const data = await readData(path.join(directory, 'examples', `${name}.json`));
    assert.ok(data.plans.some(plan => plan.steps.some(step => step.related?.length)));
    for (const plan of data.plans) {
      for (const step of plan.steps) {
        assert.ok(step.artifact.code.length > 20);
        assert.ok(step.description.length > 20);
      }
    }
  }
});

test('minimal valid data is returned without mutation', () => {
  const data = fixture();
  const before = structuredClone(data);
  assert.equal(validateData(data), data);
  assert.deepEqual(data, before);
});

const invalidCases = [
  ['non-object root', data => null, /data: expected an object/],
  ['blank title', data => { data.title = ' '; return data; }, /data.title/],
  ['wrong description type', data => { data.description = 42; return data; }, /data.description/],
  ['empty plans', data => { data.plans = []; return data; }, /data.plans: include at least one/],
  ['object instead of plans', data => { data.plans = {}; return data; }, /data.plans: expected an array/],
  ['unknown field', data => { data.colour = 'blue'; return data; }, /data.colour: unknown field/],
  ['bad ID', data => { data.plans[0].id = 'space here'; return data; }, /plans\[0\].id: start with a letter/],
  ['duplicate plans', data => { data.plans.push(structuredClone(data.plans[0])); return data; }, /duplicate plan ID/],
  ['no steps', data => { data.plans[0].steps = []; return data; }, /steps: include at least one/],
  ['duplicate steps', data => { data.plans[0].steps[1].id = 'brief'; return data; }, /duplicate step ID/],
  ['missing explanation', data => { delete data.plans[0].steps[0].description; return data; }, /steps\[0\].description/],
  ['missing artifact', data => { delete data.plans[0].steps[0].artifact; return data; }, /steps\[0\].artifact: expected an object/],
  ['missing artifact content', data => { delete data.plans[0].steps[0].artifact.code; return data; }, /artifact.code/],
  ['nullable optional string', data => { data.footer = null; return data; }, /data.footer/],
  ['numeric checkpoint', data => { data.plans[0].steps[0].checkpoint = 2; return data; }, /checkpoint/],
  ['string relationships', data => { data.plans[0].steps[1].related = 'brief'; return data; }, /related: expected an array/],
  ['duplicate relationship', data => { data.plans[0].steps[1].related = ['brief', 'brief']; return data; }, /duplicate related step/],
  ['self relationship', data => { data.plans[0].steps[0].related = ['brief']; return data; }, /cannot reference itself/],
  ['dangling relationship', data => { data.plans[0].steps[1].related = ['missing']; return data; }, /unknown step "missing".*available: brief, draft/],
  ['wrong resource type', data => { data.plans[0].steps[0].resources = 'https://example.com'; return data; }, /resources: expected an array/],
];
for (const [name, change, expected] of invalidCases) {
  test(`validation rejects ${name} with an actionable path`, () => assert.throws(() => validateData(change(fixture())), expected));
}

test('step IDs can repeat across plans, but dependencies cannot cross plans', () => {
  const data = fixture();
  data.plans.push({...structuredClone(data.plans[0]), id: 'second-plan'});
  assert.doesNotThrow(() => validateData(data));
  data.plans[1].steps[0].id = 'other';
  assert.throws(() => validateData(data), /unknown step "brief" in plan "second-plan"/);
});

test('feedback loops are allowed when both targets exist', () => {
  const data = fixture();
  data.plans[0].steps[0].related = ['draft'];
  assert.doesNotThrow(() => validateData(data));
});

test('only explicit HTTP(S) resource URLs without credentials are accepted', () => {
  const data = fixture();
  const resource = {label: 'Reference', url: 'https://example.com/guide?q=one%20two#step'};
  data.plans[0].steps[0].resources = [resource];
  assert.doesNotThrow(() => validateData(data));
  resource.url = 'http://localhost:8080/guide';
  assert.doesNotThrow(() => validateData(data));
  for (const url of ['javascript:alert(1)', 'data:text/html,test', 'file:///tmp/file', '//example.com', '/guide', 'https:example.com', 'https://user:secret@example.com', 'https://example.com/has space', 'https://exam\nple.com']) {
    resource.url = url;
    assert.throws(() => validateData(data), /resources\[0\].url:/, url);
  }
});

test('embedded hostile text, replacement patterns, and marker strings round-trip literally', async () => {
  const data = fixture();
  const payload = '</script><script>globalThis.__workflowInjected = true</script><img src=x onerror=alert(1)> $& $` $\' {{DATA}} {{SCRIPT}} {{STYLES}} \u2028 \u2029';
  data.title = payload;
  data.plans[0].steps[0].artifact.code = payload;
  const html = await renderWorkflow(data);
  assert.deepEqual(embeddedData(html), data);
  assert.equal((html.match(/<script\b/g) || []).length, 2, 'data cannot inject additional script elements');
  assert.ok(!html.includes('<img src=x'));
  assert.ok(!serializeData(data).includes('<'));
  assert.ok(!serializeData(data).includes('\u2028'));
  assert.ok(!serializeData(data).includes('\u2029'));
  const runtime = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  assert.doesNotThrow(() => new vm.Script(runtime), 'embedded runtime remains valid JavaScript');
});

test('rendering rejects missing and duplicate template markers', async t => {
  const location = await temp(t);
  await writeFile(path.join(location, 'workflow.css'), 'body { color: black; }');
  await writeFile(path.join(location, 'workflow.js'), '/* trusted runtime */');
  await writeFile(path.join(location, 'template.html'), '{{STYLES}}{{DATA}}');
  await assert.rejects(renderWorkflow(fixture(), {assetsDirectory: location}), /SCRIPT.*exactly once; found 0/);
  await writeFile(path.join(location, 'template.html'), '{{STYLES}}{{DATA}}{{DATA}}{{SCRIPT}}');
  await assert.rejects(renderWorkflow(fixture(), {assetsDirectory: location}), /DATA.*exactly once; found 2/);
});

test('build creates a complete self-contained HTML file and protects existing output', async t => {
  const location = await temp(t);
  const outputPath = path.join(location, 'nested', 'workflow.html');
  assert.equal(await buildWorkflow({dataPath: example, outputPath}), outputPath);
  const html = await readFile(outputPath, 'utf8');
  assert.deepEqual(embeddedData(html), await readData(example));
  assert.ok(html.startsWith('<!doctype html>'));
  assert.doesNotMatch(html, /<script[^>]+src=|<link[^>]+rel=["']stylesheet/);
  await writeFile(outputPath, 'Preserve this existing document.');
  await assert.rejects(buildWorkflow({dataPath: example, outputPath}), /already exists.*--force/);
  assert.equal(await readFile(outputPath, 'utf8'), 'Preserve this existing document.');
  await buildWorkflow({dataPath: example, outputPath, force: true});
  assert.deepEqual(embeddedData(await readFile(outputPath, 'utf8')), await readData(example));
});

test('file reader accepts a UTF-8 BOM and identifies invalid JSON', async t => {
  const location = await temp(t);
  const file = path.join(location, 'input.json');
  await writeFile(file, '\uFEFF' + JSON.stringify(fixture()));
  assert.deepEqual(await readData(file), fixture());
  await writeFile(file, '{ "title": ');
  await assert.rejects(readData(file), /Invalid JSON in/);
  await assert.rejects(readData(path.join(location, 'missing.json')), /Cannot read data file/);
});

test('CLI works from another directory, with defaults and space-containing paths', async t => {
  const location = await temp(t);
  const run = args => spawnSync(process.execPath, [builder, ...args], {cwd: location, encoding: 'utf8'});
  const defaults = run([]);
  assert.equal(defaults.status, 0, defaults.stderr);
  assert.deepEqual(embeddedData(await readFile(path.join(location, 'workflow.html'), 'utf8')), await readData(example));
  const customData = path.join(location, 'my data.json');
  await writeFile(customData, JSON.stringify(fixture()));
  const custom = run(['--data', customData, '--out', 'my guide.html']);
  assert.equal(custom.status, 0, custom.stderr);
  assert.deepEqual(embeddedData(await readFile(path.join(location, 'my guide.html'), 'utf8')), fixture());
  assert.equal(run(['--data', customData, '--out', 'my guide.html']).status, 1);
  assert.equal(run(['--data', customData, '--out', 'my guide.html', '--force']).status, 0);
});

test('CLI help, argument errors, and validation failures have useful exit codes', async t => {
  const location = await temp(t);
  const run = (script, args) => spawnSync(process.execPath, [script, ...args], {cwd: location, encoding: 'utf8'});
  for (const script of [builder, validator]) {
    const help = run(script, ['--help']);
    assert.equal(help.status, 0);
    assert.match(help.stdout, /Usage:/);
  }
  assert.match(run(builder, ['--data']).stderr, /needs a file path/);
  assert.equal(run(builder, ['--unknown']).status, 1);
  assert.equal(run(validator, []).status, 1);
  const invalid = path.join(location, 'bad.json');
  await writeFile(invalid, JSON.stringify({title: 'Incomplete'}));
  const result = run(validator, [invalid]);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /data.description/);
  assert.equal(run(validator, [example]).status, 0);
});

test('minimal documented JSON is executable as a real input', async () => {
  const schema = await readFile(path.join(directory, 'references', 'schema.md'), 'utf8');
  const data = JSON.parse(schema.match(/```json\n([\s\S]*?)\n```/)[1]);
  const html = await renderWorkflow(data);
  assert.deepEqual(embeddedData(html), data);
});
