import { IRenderMime } from "@jupyterlab/rendermime-interfaces";
import { graphviz, Graphviz } from "d3-graphviz";

import Slider from "@material-ui/core/Slider";
import Tooltip from "@material-ui/core/Tooltip";
import PopperJs from "popper.js";

import * as React from "react";

import * as d3transiion from "d3-transition";
import * as d3ease from "d3-ease";
import { ReactWidget } from "@jupyterlab/apputils";

/**
 * The default mime type for the extension.
 */
const MIME_TYPE = "application/x.typez.graph+json";

/**
 * This is a seperate type, of the compiled typez states as graphviz
 */
type TypezGraph = {
  initial: string;
  states: Array<{
    graph: string;
    rule: string;
    label: string | null;
  }>;
};

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
  graph,
  onChange
}: {
  graph: TypezGraph;
  onChange: (node: string) => void;
}) {
  // selected index, from the right
  const [selected, setSelected] = React.useState<number>(0);
  const i = graph.states.length - selected;
  React.useEffect(() => {
    if (i === 0) {
      onChange(graph.initial);
    } else {
      onChange(graph.states[i - 1].graph);
    }
  }, [graph, selected]);

  return (
    <Slider
      valueLabelFormat={value => `YO!${value}`}
      ValueLabelComponent={({ children, open, value }) => (
        <ValueLabelComponent
          children={children}
          open={open}
          value={
            value === 0
              ? "initial"
              : graph.states[value - 1].label || graph.states[value - 1].rule
          }
        />
      )}
      step={1}
      valueLabelDisplay="on"
      value={i}
      max={graph.states.length}
      onChange={(_, newValue) =>
        setSelected(graph.states.length - (newValue as any))
      }
      marks={[
        { value: 0, label: "initial" },
        ...graph.states.map(({ label }, idx) => ({
          value: idx + 1,
          label
        }))
      ]}
    />
  );
}

const t = d3transiion
  .transition("main")
  .ease(d3ease.easeQuadInOut)
  .delay(100)
  .duration(600);
export function GraphvizComponent({ dot }: { dot: string }) {
  const el = React.useRef<HTMLDivElement>(null);
  const [graph, setGraph] = React.useState<null | Graphviz<any, any, any, any>>(
    null
  );

  React.useEffect(() => {
    setGraph(
      graphviz(el.current!, {
        keyMode: "id",
        // https://github.com/magjac/d3-graphviz#performance
        tweenShapes: false,
        tweenPaths: false,
        height: 
      }).transition(t as any)
    );
  }, [el.current]);

  React.useEffect(() => {
    if (!graph) {
      return;
    }
    graph.renderDot(dot);
  }, [graph, dot]);

  return <div ref={el} />;
}

export function GraphComponent({ graph }: { graph: TypezGraph }) {
  const [dot, setDot] = React.useState<string>(graph.initial);
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
        <SelectState graph={graph} onChange={setDot} />
      </div>
      <GraphvizComponent dot={dot} />
    </div>
  );
}

class OutputWidget extends ReactWidget implements IRenderMime.IRenderer {
  /**
   * Render typez-graph into this widget's node.
   */
  async renderModel(model: IRenderMime.IMimeModel): Promise<void> {
    this.graph = model.data[MIME_TYPE] as TypezGraph;
    this.update();
  }

  render() {
    if (!this.graph) {
      return <></>;
    }
    return <GraphComponent graph={this.graph} />;
  }

  graph: TypezGraph | null = null;
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
