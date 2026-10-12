// SVG <use> has stricter cross-origin rules than normal images. Put the pinned
// symbols in this document and rewrite references to local fragment IDs.
export async function installLocalSprites() {
    const media = await (await fetch(new URL("./media-assets.json", import.meta.url))).json();
    const paths = media.filter(path => /(?:-sprite-|-symbol-).*\.svg$/.test(path));
    const references = new Map();
    const container = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    container.setAttribute("aria-hidden", "true");
    container.style.cssText = "position:absolute;width:0;height:0;overflow:hidden";
    for (const path of paths) {
        const filename = path.split("/").pop();
        const response = await fetch(new URL("./media/" + filename, import.meta.url));
        if (!response.ok) throw new Error("Missing bundled sprite " + filename);
        const svg = new DOMParser().parseFromString(await response.text(), "image/svg+xml");
        if (svg.querySelector("parsererror")) throw new Error("Invalid bundled sprite " + filename);
        const prefix = "classic-" + filename.replace(/[^a-zA-Z0-9_-]/g, "-") + "-";
        for (const element of svg.querySelectorAll("[id]")) {
            references.set(path + "#" + element.id, "#" + prefix + element.id);
            element.id = prefix + element.id;
        }
        // Preserve gradients, clip paths and nested symbol references after
        // moving several independent SVG files into one shared document.
        for (const element of svg.querySelectorAll("*")) {
            for (const attribute of Array.from(element.attributes)) {
                let value = attribute.value.replace(/url\(#([^)]+)\)/g, (_, id) => "url(#" + prefix + id + ")");
                if ((attribute.localName === "href") && value.startsWith("#")) value = "#" + prefix + value.slice(1);
                if (value !== attribute.value) element.setAttributeNS(attribute.namespaceURI, attribute.name, value);
            }
        }
        container.append(...Array.from(svg.documentElement.children));
    }
    document.body.append(container);
    const rewrite = use => {
        const href = use.getAttribute("href") || use.getAttributeNS("http://www.w3.org/1999/xlink", "href");
        if (!href || href.startsWith("#")) return;
        const url = new URL(href, location.href);
        const path = url.pathname.replace(/^\/production-main/, "");
        const replacement = references.get(path + url.hash);
        if (!replacement) return;
        use.setAttribute("href", replacement);
        use.removeAttributeNS("http://www.w3.org/1999/xlink", "href");
    };
    const observer = new MutationObserver(records => {
        for (const record of records) {
            if (record.type === "attributes") rewrite(record.target);
            for (const node of record.addedNodes) {
                if (!(node instanceof Element)) continue;
                if (node.localName === "use") rewrite(node);
                for (const use of node.querySelectorAll("use")) rewrite(use);
            }
        }
    });
    observer.observe(document.body, {childList:true,subtree:true,attributes:true,attributeFilter:["href","xlink:href"]});
    for (const use of document.querySelectorAll("use")) rewrite(use);
}
