/* Extract call sites, not just URL strings, from a frozen public asset graph.
 * Install acorn 8.15.0 and acorn-walk 8.3.4 into a throwaway tools directory,
 * then pass that directory's node_modules as the second argument.
 */
const fs = require('node:fs');
const path = require('node:path');
const root = process.argv[2];
const parserRoot = process.argv[3];
const acorn = require(path.join(parserRoot, 'acorn'));
const walk = require(path.join(parserRoot, 'acorn-walk'));
const methods = new Set(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']);

function property(node) {
    if (!node) return '';
    return node.name ?? node.value ?? '';
}

function stringValue(node) {
    if (!node) return null;
    if (node.type === 'Literal' && typeof node.value === 'string') return node.value;
    if (node.type === 'TemplateLiteral') return node.quasis.map((part, i) => part.value.cooked + (i < node.expressions.length ? '{dynamic}' : '')).join('');
    if (node.type === 'BinaryExpression' && node.operator === '+') {
        const left = stringValue(node.left);
        const right = stringValue(node.right);
        if (left !== null || right !== null) return (left ?? '{dynamic}') + (right ?? '{dynamic}');
    }
    return null;
}

function fields(node, prefix = '', resolve = value => value, depth = 0) {
    if (depth > 5) return [prefix + '<depth-limit>'];
    node = resolve(node);
    if (!node || node.type !== 'ObjectExpression') return [];
    const result = [];
    for (const entry of node.properties) {
        if (entry.type === 'SpreadElement') {
            result.push(prefix + '<spread>');
            continue;
        }
        const key = entry.computed ? '<computed-key>' : String(property(entry.key));
        result.push(prefix + key);
        const value = resolve(entry.value);
        result.push(...fields(value, prefix + key + '.', resolve, depth + 1));
        if (['body', 'params', 'query', 'path', 'header'].includes(key) && value && value.type !== 'ObjectExpression') result.push(prefix + key + '.<dynamic>');
    }
    return result.sort();
}

function inspect(label) {
    const calls = [], literals = [], resources = [], unresolved = [], errors = [];
    const files = fs.readdirSync(path.join(root, label)).filter(name => name.endsWith('.js')).sort();
    for (const file of files) {
        const source = fs.readFileSync(path.join(root, label, file), 'utf8');
        let ast;
        try {
            ast = acorn.parse(source, {ecmaVersion: 'latest', sourceType: 'module', allowAwaitOutsideFunction: true});
        } catch (error) {
            errors.push({file, error: error.message});
            continue;
        }
        // Resolve simple immutable string/URL aliases, and literal option objects
        // passed by name. Never pretend arbitrary expressions are statically known.
        const bindings = new Map();
        const isScope = node => node.type === 'Program' || node.type === 'BlockStatement' || /Function/.test(node.type);
        walk.ancestor(ast, {VariableDeclarator(node, ancestors) {
            if (node.id.type !== 'Identifier' || !node.init) return;
            const scope = ancestors.filter(isScope).at(-1);
            if (!bindings.has(scope)) bindings.set(scope, new Map());
            bindings.get(scope).set(node.id.name, node.init);
        }});
        function resolve(node, ancestors, depth = 0) {
            if (!node || node.type !== 'Identifier') return node;
            if (depth > 4) return node;
            for (const scope of ancestors.filter(isScope).reverse()) {
                const value = bindings.get(scope)?.get(node.name);
                if (value && value.start < node.start) return resolve(value, ancestors, depth + 1);
                // A parameter shadows bindings in all outer scopes.
                if (scope.params?.some(p => p.type === 'Identifier' && p.name === node.name)) return node;
            }
            return node;
        }
        walk.ancestor(ast, {
            ObjectExpression(node) {
                const action = node.properties.find(p => property(p.key) === 'action');
                const method = node.properties.find(p => property(p.key) === 'method');
                const route = stringValue(action?.value);
                if (!route?.startsWith('/')) return;
                calls.push({method:(stringValue(method?.value) ?? 'GET').toUpperCase(),route,kind:'html-form',file,offset:node.start,fields:[],options:'',call:source.slice(node.start,node.end),context:source.slice(Math.max(0,node.start-100),node.end+100)});
            },
            Literal(node) {
                if (typeof node.value === 'string' && /(?:\/api\/|\/ws\/|wss?:\/\/)/.test(node.value)) literals.push({file, offset: node.start, value: node.value});
                if (typeof node.value === 'string' && /\/static3\/(?:media|soundfonts)\//.test(node.value)) resources.push({file,offset:node.start,value:node.value});
            },
            TemplateLiteral(node) {
                const value = stringValue(node);
                if (value && /(?:\/api\/|\/ws\/|wss?:\/\/)/.test(value)) literals.push({file, offset: node.start, value});
                if (value && /\/static3\/(?:media|soundfonts)\//.test(value)) resources.push({file,offset:node.start,value});
            },
            CallExpression(node, ancestors) {
                const callee = node.callee;
                let method, routeNode, options, kind;
                if (callee.type === 'MemberExpression' && methods.has(property(callee.property))) {
                    method = property(callee.property); routeNode = node.arguments[0]; options = node.arguments[1]; kind = 'typed-http';
                } else if ((callee.type === 'Identifier' && callee.name === 'fetch') || (callee.type === 'MemberExpression' && property(callee.property) === 'fetch')) {
                    method = 'GET'; routeNode = node.arguments[0]; options = node.arguments[1]; kind = 'fetch';
                    const resolved = resolve(options, ancestors);
                    const methodField = resolved?.properties?.find(p => property(p.key) === 'method');
                    if (methodField) method = stringValue(methodField.value) ?? 'DYNAMIC';
                    else if (options && resolved.type !== 'ObjectExpression') method = 'DYNAMIC';
                } else if (callee.type === 'MemberExpression' && property(callee.property) === 'open' && methods.has(stringValue(node.arguments[0]))) {
                    method = stringValue(node.arguments[0]); routeNode = node.arguments[1]; kind = 'xhr';
                } else if (callee.type === 'MemberExpression' && property(callee.property) === 'sendBeacon') {
                    method = 'POST'; routeNode = node.arguments[0]; kind = 'beacon';
                } else return;
                const route = stringValue(routeNode);
                const resolved = resolve(options, ancestors);
                const record = {
                    method, route, kind, file, offset: node.start,
                    fields: fields(resolved, '', value => resolve(value, ancestors)), optionsViaIdentifier: options?.type === 'Identifier',
                    options: resolved ? source.slice(resolved.start, resolved.end) : '',
                    call: source.slice(node.start, node.end),
                    context: source.slice(Math.max(0, node.start - 160), node.end + 300),
                };
                if (route === null) unresolved.push(record); else calls.push(record);
            },
            NewExpression(node) {
                if (node.callee.type !== 'Identifier' || !['WebSocket', 'EventSource', 'WebSocketClient', 'Worker', 'SharedWorker'].includes(node.callee.name)) return;
                const route = stringValue(node.arguments[0]);
                const record = {method: node.callee.name, route, kind: 'transport', file, offset: node.start, fields: fields(node.arguments[0]), call: source.slice(node.start, node.end), context: source.slice(Math.max(0,node.start-120),node.end+160)};
                if (route === null) unresolved.push(record); else calls.push(record);
            },
        });
    }
    return {files: files.length, parsed: files.length - errors.length, errors, calls, literals, resources, unresolved};
}

const result = {scope: 'AST call sites and remaining API/WS literals. Field equality is not semantic or server compatibility proof.', july: inspect('july'), current: inspect('current')};
fs.writeFileSync(path.join(root, 'api-calls.json'), JSON.stringify(result, null, 2) + '\n');
for (const label of ['july','current']) {
    const item = result[label];
    console.log(label, JSON.stringify({files:item.files,parsed:item.parsed,calls:item.calls.length,literals:item.literals.length,unresolved:item.unresolved.length,errors:item.errors}));
}
