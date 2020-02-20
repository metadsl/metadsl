/**
 * Inspired by https://github.com/plotly/react-cytoscapejs
 * but simplifed for my use case, because I was getting bugs on that ones
 * adding and removing logic.
 */

import {
  ElementsDefinition,
  Stylesheet,
  BaseLayoutOptions,
  AnimatedLayoutOptions
} from "cytoscape";
import Cytoscape from "cytoscape";
import Dagre from "cytoscape-dagre";
import Klay from "cytoscape-klay";
import Elk from "cytoscape-elk-saul";
import * as React from "react";

Cytoscape.use(Elk);
Cytoscape.use(Dagre);
Cytoscape.use(Klay);

type DagreLayoutOption = {
  name: "dagre";
  nodeDimensionsIncludeLabels?: boolean;
  nodeSep?: number; // the separation between adjacent nodes in the same rank
  edgeSep?: number; // the separation between adjacent edges in the same rank
  rankSep?: number; // the separation between each rank in the layout
  rankDir?: "TB" | "LR"; // 'TB' for top to bottom flow, 'LR' for left to right,
  ranker?: "network-simplex" | "tight-tree" | "longest-path"; // Type of algorithm to assign a rank to each node in the input graph. Possible values: 'network-simplex', 'tight-tree' or 'longest-path'
  minLen?: (edge: any) => number; // number of ranks to keep between the source and target of the edge
  edgeWeight?: (edge: any) => number; // higher weight edges are generally made shorter and straighter than lower weight edges
} & BaseLayoutOptions &
  AnimatedLayoutOptions;

const defaultKlay = {
  // Following descriptions taken from http://layout.rtsys.informatik.uni-kiel.de:9444/Providedlayout.html?algorithm=de.cau.cs.kieler.klay.layered
  addUnnecessaryBendpoints: false, // Adds bend points even if an edge does not change direction.
  aspectRatio: 1.6, // The aimed aspect ratio of the drawing, that is the quotient of width by height
  borderSpacing: 20, // Minimal amount of space to be left to the border
  compactComponents: false, // Tries to further compact components (disconnected sub-graphs).
  crossingMinimization: "LAYER_SWEEP", // Strategy for crossing minimization.
  /* LAYER_SWEEP The layer sweep algorithm iterates multiple times over the layers, trying to find node orderings that minimize the number of crossings. The algorithm uses randomization to increase the odds of finding a good result. To improve its results, consider increasing the Thoroughness option, which influences the number of iterations done. The Randomization seed also influences results.
    INTERACTIVE Orders the nodes of each layer by comparing their positions before the layout algorithm was started. The idea is that the relative order of nodes as it was before layout was applied is not changed. This of course requires valid positions for all nodes to have been set on the input graph before calling the layout algorithm. The interactive layer sweep algorithm uses the Interactive Reference Point option to determine which reference point of nodes are used to compare positions. */
  cycleBreaking: "GREEDY", // Strategy for cycle breaking. Cycle breaking looks for cycles in the graph and determines which edges to reverse to break the cycles. Reversed edges will end up pointing to the opposite direction of regular edges (that is, reversed edges will point left if edges usually point right).
  /* GREEDY This algorithm reverses edges greedily. The algorithm tries to avoid edges that have the Priority property set.
    INTERACTIVE The interactive algorithm tries to reverse edges that already pointed leftwards in the input graph. This requires node and port coordinates to have been set to sensible values.*/
  direction: "UNDEFINED", // Overall direction of edges: horizontal (right / left) or vertical (down / up)
  /* UNDEFINED, RIGHT, LEFT, DOWN, UP */
  edgeRouting: "ORTHOGONAL", // Defines how edges are routed (POLYLINE, ORTHOGONAL, SPLINES)
  edgeSpacingFactor: 0.5, // Factor by which the object spacing is multiplied to arrive at the minimal spacing between edges.
  feedbackEdges: false, // Whether feedback edges should be highlighted by routing around the nodes.
  fixedAlignment: "NONE", // Tells the BK node placer to use a certain alignment instead of taking the optimal result.  This option should usually be left alone.
  /* NONE Chooses the smallest layout from the four possible candidates.
    LEFTUP Chooses the left-up candidate from the four possible candidates.
    RIGHTUP Chooses the right-up candidate from the four possible candidates.
    LEFTDOWN Chooses the left-down candidate from the four possible candidates.
    RIGHTDOWN Chooses the right-down candidate from the four possible candidates.
    BALANCED Creates a balanced layout from the four possible candidates. */
  inLayerSpacingFactor: 1.0, // Factor by which the usual spacing is multiplied to determine the in-layer spacing between objects.
  layoutHierarchy: false, // Whether the selected layouter should consider the full hierarchy
  linearSegmentsDeflectionDampening: 0.3, // Dampens the movement of nodes to keep the diagram from getting too large.
  mergeEdges: false, // Edges that have no ports are merged so they touch the connected nodes at the same points.
  mergeHierarchyCrossingEdges: true, // If hierarchical layout is active, hierarchy-crossing edges use as few hierarchical ports as possible.
  nodeLayering: "NETWORK_SIMPLEX", // Strategy for node layering.
  /* NETWORK_SIMPLEX This algorithm tries to minimize the length of edges. This is the most computationally intensive algorithm. The number of iterations after which it aborts if it hasn't found a result yet can be set with the Maximal Iterations option.
    LONGEST_PATH A very simple algorithm that distributes nodes along their longest path to a sink node.
    INTERACTIVE Distributes the nodes into layers by comparing their positions before the layout algorithm was started. The idea is that the relative horizontal order of nodes as it was before layout was applied is not changed. This of course requires valid positions for all nodes to have been set on the input graph before calling the layout algorithm. The interactive node layering algorithm uses the Interactive Reference Point option to determine which reference point of nodes are used to compare positions. */
  nodePlacement: "BRANDES_KOEPF", // Strategy for Node Placement
  /* BRANDES_KOEPF Minimizes the number of edge bends at the expense of diagram size: diagrams drawn with this algorithm are usually higher than diagrams drawn with other algorithms.
    LINEAR_SEGMENTS Computes a balanced placement.
    INTERACTIVE Tries to keep the preset y coordinates of nodes from the original layout. For dummy nodes, a guess is made to infer their coordinates. Requires the other interactive phase implementations to have run as well.
    SIMPLE Minimizes the area at the expense of... well, pretty much everything else. */
  randomizationSeed: 1, // Seed used for pseudo-random number generators to control the layout algorithm; 0 means a new seed is generated
  routeSelfLoopInside: false, // Whether a self-loop is routed around or inside its node.
  separateConnectedComponents: true, // Whether each connected component should be processed separately
  spacing: 20, // Overall setting for the minimal amount of space to be left between objects
  thoroughness: 7 // How much effort should be spent to produce a nice layout..
};

type KlayLayout = {
  name: "klay";
  klay: Partial<typeof defaultKlay>;
} & BaseLayoutOptions &
  AnimatedLayoutOptions;

export const dagreLayout: DagreLayoutOption = {
  name: "dagre",
  ranker: "longest-path",
  nodeDimensionsIncludeLabels: true,
  animate: true,
  animationDuration: 900
};

export const klayLayout: KlayLayout = {
  name: "klay",
  // nodeDimensionsIncludeLabels: true,
  animate: true,
  animationDuration: 900,
  klay: {
    // nodeLayering: "INTERACTIVE",
    // direction: "VERTICAL"
  }
};

const layout = {
  name: "elk",
  nodeDimensionsIncludeLabels: true, // Boolean which changes whether label dimensions are included when calculating node dimensions
  fit: true, // Whether to fit
  padding: 40, // Padding on fit
  animate: true, // Whether to transition the node positions
  animationDuration: 900, // Duration of animation in ms if enabled
  animationEasing: "ease-in-out-cubic",
  // animationEasing: undefined, // Easing of animation if enabled
  // transform: function( node, pos ){ return pos; }, // A function that applies a transform to the final node position
  // ready: undefined, // Callback on layoutready
  // stop: undefined, // Callback on layoutstop
  elk: {
    // All options are available at http://www.eclipse.org/elk/reference.html
    // 'org.eclipse.elk.' can be dropped from the Identifier
    // Or look at demo.html for an example.
    // Enums use the name of the enum e.g.
    // searchOrder: "BFS",
    zoomToFit: true,
    algorithm: "conn.gmf.layouter.Draw2D",
    "org.eclipse.elk.direction": "DOWN"
  }
  // priority: function( edge ){ return null; }, // Edges with a non-nil value are skipped when geedy edge cycle breaking is enabled
};
// export const layout:
//   | LayoutOptions
//   | DagreLayoutOption
//   | KlayLayout = klayLayout;

const style: Stylesheet[] = [
  {
    selector: "node",
    style: {
      label: "data(label)",
      "text-valign": "center",
      "text-halign": "right",
      "text-wrap": "wrap"
      // "text-outline-color": "#555",
      // "text-outline-width": "2px",
      // color: "#fff"
      // "min-zoomed-font-size": 13
      // "text-max-width": "400px"
    }
  },
  {
    selector: "edge",
    style: {
      // haystack so multiple edges don't overlap
      // "curve-style": "segments",
      // "haystack-radius": 0.2,
      "curve-style": "straight",
      "target-arrow-shape": "triangle",
      "target-arrow-fill": "filled",
      opacity: "0.5"
    } as any
  },
  {
    selector: ".hidden",
    style: {
      display: "none"
    }
  }
];

export default function CytoscapeComponent({
  elements
}: {
  elements: ElementsDefinition;
}) {
  const ref = React.useRef(null);
  const cy = React.useRef<Cytoscape.Core | null>(null);

  /**
   * Only show descendents of selected nodes.
   */
  const updateSelection = () => {
    const current = cy.current!;
    const selected = current.$(":selected");
    let shown: cytoscape.CollectionReturnValue;
    if (selected.length === 0) {
      // If none selected, set all nodes to visible
      shown = current.$("");
    } else {
      // Otherwise only set those as successors of selected
      shown = selected.union(selected.successors());
    }
    shown.classes("");
    shown.absoluteComplement().classes("hidden");
    shown.layout(layout as any).run();
  };

  React.useEffect(() => {
    if (!ref) {
      return;
    }
    cy.current = Cytoscape({
      container: ref.current!,
      style
      // pixelRatio: 1.0
      // hideEdgesOnViewport: true
    });
    cy.current.on("select", () => {
      updateSelection();
    });
    cy.current.on("unselect", () => {
      updateSelection();
    });
    return () => {
      if (cy.current) {
        cy.current.destroy();
      }
    };
  }, [ref]);

  // Update elements and layout
  React.useEffect(() => {
    if (!cy.current) {
      return;
    }
    cy.current.json({ elements });
    updateSelection();
  }, [cy.current, elements]);

  return <div style={{ height: "800px" }} ref={ref} />;
}
