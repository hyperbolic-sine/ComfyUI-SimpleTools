// Resolution Selector - live "W x H" readout under the node.
//
// The size table lives in the Python backend (single source of truth) and is
// fetched once per session from OPTIONS_ROUTE. If the route is unavailable the
// node still works, only the readout stays empty.

import { app } from "../../scripts/app.js";

const OPTIONS_ROUTE = "/simpletools/resolution_selector/options";

// Current key first, legacy keys kept so older workflows keep the readout.
const NODE_NAMES = [
    "SimpleResolutionSelector",
    "ResolutionSelectorJWB",
    "ResolutionSelectorMie",
];

const PLACEHOLDER = "…";

let optionsPromise = null;

function loadOptions() {
    if (!optionsPromise) {
        optionsPromise = fetch(OPTIONS_ROUTE)
            .then((response) => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .catch((error) => {
                console.warn(
                    "[SimpleTools] resolution table unavailable, size readout disabled:",
                    error
                );
                optionsPromise = null; // allow a retry on the next node created
                return null;
            });
    }
    return optionsPromise;
}

app.registerExtension({
    name: "SimpleTools.ResolutionSelector",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!NODE_NAMES.includes(nodeData.name)) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);

            const tierWidget = this.widgets?.find((w) => w.name === "resolution");
            const ratioWidget = this.widgets?.find((w) => w.name === "aspect_ratio");
            if (!tierWidget || !ratioWidget) return result;

            // Read-only DOM readout: not serialized, not part of the graph data.
            const readout = document.createElement("div");
            readout.style.textAlign = "center";
            readout.style.fontWeight = "bold";
            readout.style.padding = "4px 0";
            readout.style.fontSize = "14px";
            readout.style.color = "#00a86b";
            readout.textContent = PLACEHOLDER;
            this.addDOMWidget("output_resolution", "div", readout, { serialize: false });

            let table = null;

            const syncDisplay = () => {
                const size = table?.[tierWidget.value]?.[ratioWidget.value];
                if (!size || size.length !== 2) return;
                const text = `${size[0]}×${size[1]}`;
                if (readout.textContent === text) return;
                readout.textContent = text;
                app.graph.setDirtyCanvas(true);
            };

            // Refresh the readout whenever either dropdown changes.
            for (const widget of [tierWidget, ratioWidget]) {
                const original = widget.callback;
                widget.callback = function (value, ...rest) {
                    const ret = original?.apply(this, [value, ...rest]);
                    syncDisplay();
                    return ret;
                };
            }

            // Widget values restored from a loaded workflow do not always fire
            // callbacks, so refresh once after configure as well.
            this._rsSyncDisplay = syncDisplay;
            const onConfigure = this.onConfigure;
            this.onConfigure = function () {
                const ret = onConfigure?.apply(this, arguments);
                syncDisplay();
                return ret;
            };

            loadOptions().then((data) => {
                table = data;
                syncDisplay();
            });

            return result;
        };
    },
});
