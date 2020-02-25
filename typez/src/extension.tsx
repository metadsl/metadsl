import { ReactWidget } from "@jupyterlab/apputils";
import { IRenderMime } from "@jupyterlab/rendermime-interfaces";
import * as React from "react";
import GraphComponent from "./GraphComponent";
import { Typez } from "./schema";

/**
 * The default mime type for the extension.
 */
const MIME_TYPE = "application/x.typez+json";

class OutputWidget extends ReactWidget implements IRenderMime.IRenderer {
  /**
   * Render typez-graph into this widget's node.
   */
  async renderModel(model: IRenderMime.IMimeModel): Promise<void> {
    this.typez = model.data[MIME_TYPE] as Typez;
    this.update();
  }

  render() {
    if (!this.typez) {
      return <></>;
    }
    return <GraphComponent typez={this.typez} />;
  }

  typez: Typez | null = null;
}

/**
 * A mime renderer factory for typez-graph data.
 */
const rendererFactory: IRenderMime.IRendererFactory = {
  safe: true,
  mimeTypes: [MIME_TYPE],
  createRenderer: () => new OutputWidget()
};

/**
 * Extension definition.
 */
const extension: IRenderMime.IExtension = {
  id: "typez-graph:plugin",
  rendererFactory,
  // So it renders before JSON
  rank: -10,
  dataType: "json",
  fileTypes: [
    {
      name: "typez-graph",
      mimeTypes: [MIME_TYPE],
      extensions: ["typez.json"]
    }
  ],
  documentWidgetFactoryOptions: {
    name: "typez viewer",
    primaryFileType: "typez-graph",
    fileTypes: ["typez-graph"],
    defaultFor: ["typez-graph"]
  }
};
export default extension;
