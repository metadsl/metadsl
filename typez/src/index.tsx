import { IRenderMime } from "@jupyterlab/rendermime-interfaces";

import Slider from "@material-ui/core/Slider";
import Tooltip from "@material-ui/core/Tooltip";
import PopperJs from "popper.js";

import * as React from "react";

import { ReactWidget } from "@jupyterlab/apputils";
import { Typez } from "./schema";
import { ElementsDefinition } from "cytoscape";
import CytoscapeComponent from "./CytoscapeComponent";

/**
 * The default mime type for the extension.
 */
const MIME_TYPE = "application/x.typez+json";

function ValueLabelComponent(props: {
  children: React.ReactElement;
  open: boolean;
  value: string;
}) {
  const { children, open, value } = props;

  const popperRef = React.useRef<PopperJs | null>(null);
  React.useEffect(() => {
    if (popperRef.current) {
      popperRef.current.update();
    }
  });

  return (
    <Tooltip
      PopperProps={{
        popperRef
      }}
      open={open}
      enterTouchDelay={0}
      placement="bottom"
      title={value}
    >
      {children}
    </Tooltip>
  );
}
export function SelectState({
  typez: { states },
  onChange
}: {
  typez: Typez;
  onChange: (node: string) => void;
}) {
  // selected index, from the right
  const [selected, setSelected] = React.useState<number>(0);
  const n = states?.states?.length || 0;
  const i = n - selected;
  React.useEffect(() => {
    if (i === 0) {
      onChange(states!.initial);
    } else {
      onChange(states!.states![i - 1]!.node);
    }
  }, [states, selected]);

  return (
    <Slider
      ValueLabelComponent={({ children, open, value }) => (
        <ValueLabelComponent
          children={children}
          open={open}
          value={
            value === 0
              ? "initial"
              : states!.states![value - 1].label ??
                states!.states![value - 1].rule
          }
        />
      )}
      step={1}
      valueLabelDisplay="on"
      value={i}
      max={n}
      onChange={(_, newValue) => setSelected(n - (newValue as any))}
      marks={[
        { value: 0, label: "initial" },
        ...(states?.states?.map(({ label }, idx) => ({
          value: idx + 1,
          label
        })) ?? [])
      ]}
    />
  );
}

function typezToCytoscape(
  nodes: Typez["nodes"],
  id: string
): ElementsDefinition {
  if (!nodes) {
    throw new Error("Must have nodes");
  }

  const elements: ElementsDefinition = { nodes: [], edges: [] };
  const seen = new Set<string>();
  const toProcess = new Set([nodes[id]]);

  for (const args of toProcess) {
    toProcess.delete(args);

    const [persistantID, node] = args;
    seen.add(persistantID);

    let label: string;
    if ("repr" in node) {
      label = node.repr;
    } else {
      label = node.function;
      for (const [childIndex, childID] of [
        ...Object.entries(node.kwargs || {}),
        ...(node.args || []).map(
          (argID, index) => [index, argID] as [number, string]
        )
      ]) {
        const childNode = nodes[childID];
        const childPersistantID = childNode[0];
        elements.edges.push({
          data: {
            source: persistantID,
            id: `${persistantID}.${childIndex}`,
            target: childPersistantID
          }
        });
        if (!seen.has(childPersistantID)) {
          toProcess.add(childNode);
        }
      }
    }
    elements.nodes.push({ data: { id: persistantID, label } });
  }
  return elements;
}

export function GraphComponent({ typez }: { typez: Typez }) {
  const [id, setID] = React.useState(typez.states!.initial);
  const elements = typezToCytoscape(typez["nodes"], id);

  return (
    <div>
      <div
        style={{
          paddingLeft: "28px",
          paddingTop: "8px",
          paddingRight: "28px",
          width: "100%",
          boxSizing: "border-box"
        }}
      >
        <SelectState typez={typez} onChange={setID} />
      </div>
      <CytoscapeComponent elements={elements} />
    </div>
  );
}

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
export const rendererFactory: IRenderMime.IRendererFactory = {
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
