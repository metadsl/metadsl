import { IRenderMime } from "@jupyterlab/rendermime-interfaces";
import { graphviz, Graphviz } from "d3-graphviz";

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

export function ShowLabels({
  shown,
  onChange
}: {
  shown: boolean;
  onChange: (show: boolean) => void;
}) {
  return (
    <label>
      <b>Only show labeled</b>
      <input
        type="checkbox"
        checked={shown}
        onChange={e => onChange(e.target.checked)}
      />
    </label>
  );
}

export function SelectState({
  graph,
  onChange,
  showLabels
}: {
  graph: TypezGraph;
  showLabels: boolean;
  onChange: (node: string) => void;
}) {
  const [selected, setSelected] = React.useState<number>(-1);
  React.useEffect(() => {
    if (selected === -1) {
      onChange(graph.initial);
    } else {
      onChange(graph.states[selected].graph);
    }
  }, [graph, selected]);
  return (
    <div>
      <div>
        <label>
          <input
            type="radio"
            value="-1"
            checked={selected === -1}
            onChange={e => (e.target.value ? setSelected(-1) : null)}
          />
          <b>Initial</b>
        </label>
      </div>
      {graph.states.map(({ rule, label }, idx) => {
        if (showLabels && !label) {
          return;
        }
        return (
          <div key={idx.toString()}>
            <label>
              <input
                type="radio"
                value={idx.toString()}
                checked={idx === selected}
                onChange={e => (e.target.value ? setSelected(idx) : null)}
              />
              {showLabels ? (
                <b>{label}</b>
              ) : (
                <>
                  {label ? <b>{label} </b> : ""}
                  <code>{rule}</code>
                </>
              )}
            </label>
          </div>
        );
      })}
    </div>
  );
}

const t = d3transiion
  .transition("main")
  .ease(d3ease.easeCubicOut)
  // .delay(100)
  .duration(300);
export function GraphvizComponent({ dot }: { dot: string }) {
  const el = React.useRef<HTMLDivElement>(null);
  const [graph, setGraph] = React.useState<null | Graphviz<any, any, any, any>>(
    null
  );

  React.useEffect(() => {
    setGraph(graphviz(el.current!));
  }, [el.current]);

  React.useEffect(() => {
    if (!graph) {
      return;
    }
    // if we have already rendered, add a transition
    if (graph.data()) {
      graph.transition(() => t).renderDot(dot);
    } else {
      graph.renderDot(dot);
    }
  }, [graph, dot]);

  return <div ref={el} />;
}

export function GraphComponent({ graph }: { graph: TypezGraph }) {
  const [dot, setDot] = React.useState<string>(graph.initial);
  const [shown, setShown] = React.useState<boolean>(true);
  return (
    <div style={{ display: "flex" }}>
      <div>
        <ShowLabels shown={shown} onChange={setShown} />
        <SelectState showLabels={shown} graph={graph} onChange={setDot} />
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
