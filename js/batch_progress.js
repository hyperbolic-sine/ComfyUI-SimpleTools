// Batch Progress - render the progress string the backend returns via ui.text.

import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "SimpleTools.BatchProgress",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData?.name !== "BatchProgress") return;

        const onExecuted = nodeType.prototype.onExecuted;

        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);

            if (!this.progressWidget) {
                this.progressWidget = ComfyWidgets["STRING"](
                    this,
                    "progress",
                    ["STRING", { multiline: true }],
                    app
                ).widget;
                this.progressWidget.inputEl.readOnly = true;
                this.progressWidget.inputEl.style.border = "none";
                this.progressWidget.inputEl.style.backgroundColor = "transparent";
                this.progressWidget.inputEl.style.textAlign = "center";
                this.progressWidget.inputEl.style.fontSize = "12px";
                this.progressWidget.inputEl.style.color = "#4fc3f7";
                this.progressWidget.inputEl.style.cursor = "default";
            }

            this.progressWidget.value = message?.text?.join("") ?? "";
            this.setSize(this.size);
        };
    },
});
