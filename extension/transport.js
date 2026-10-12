// Shared by the page and the score worker. Do not log bodies, cookies or URLs
// containing account keys. Unknown requests and all responses pass unchanged.
(() => {
    if (globalThis.songsterrClassicTransport) return;

    async function adaptRequest(input, init, baseUrl) {
        const resolved = typeof input === "string" ? new URL(input, baseUrl) : input;
        const request = new Request(resolved, init);
        const url = new URL(request.url);
        if (url.origin !== "https://www.songsterr.com") return request;

        // October explicitly asks for the lightweight list. July only consumes
        // that list; requesting result payloads would not add a result viewer.
        if (request.method === "GET" && url.pathname === "/api/contributions/transcriptions") {
            if (url.searchParams.has("withResults")) return request;
            url.searchParams.set("withResults", "false");
            return new Request(url, request);
        }

        const rename = request.method === "POST" && /^\/api\/song\/\d+\/rename$/.test(url.pathname);
        const feedback = request.method === "PATCH" && /^\/api\/rag-chat\/[^/]+\/message\/[^/]+\/feedback$/.test(url.pathname);
        if (!rename && !feedback) return request;

        // Inspect a clone so unaffected requests retain their original bytes.
        // The worker can gzip JSON before fetch; changing only plain JSON would
        // silently miss the same operation when compression is enabled.
        const encoding = request.headers.get("Content-Encoding");
        if (encoding && encoding !== "gzip") {
            throw new Error("Classic cannot adapt this request's content encoding.");
        }
        const clone = request.clone();
        const stream = encoding === "gzip" ? clone.body.pipeThrough(new DecompressionStream("gzip")) : clone.body;
        const body = JSON.parse(await new Response(stream).text());
        if (rename) {
            delete body.additionalCheckShown;
            // October labels the explanation optional. Do not invent a reason
            // on the user's behalf; preserve an explicitly supplied explanation.
            if (body.explanation === undefined) body.explanation = "";
        } else {
            delete body.source;
        }
        const headers = new Headers(request.headers);
        headers.delete("Content-Length");
        headers.delete("Content-Encoding");
        headers.set("Content-Type", "application/json");
        return new Request(request, {headers, body: JSON.stringify(body)});
    }

    const nativeFetch = globalThis.fetch.bind(globalThis);
    const baseUrl = globalThis.location.protocol === "blob:" ? globalThis.location.origin + "/" : globalThis.location.href;
    globalThis.fetch = async (input, init) => {
        const request = await adaptRequest(input, init, baseUrl);
        return nativeFetch(request);
    };
    globalThis.songsterrClassicTransport = {adaptRequest};
})();
