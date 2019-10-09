/**
 * Inspired by https://github.com/plotly/react-cytoscapejs
 * but simplifed for my use case, because I was getting bugs on that ones
 * adding and removing logic.
 */

import { ElementsDefinition, LayoutOptions, Stylesheet } from "cytoscape";
import Cytoscape from "cytoscape";
import Dagre from "cytoscape-dagre";
import * as React from "react";

Cytoscape.use(Dagre);
const layout: LayoutOptions = {
  name: "dagre",
  nodeDimensionsIncludeLabels: true,
  animate: true,
  animationDuration: 900,
};

const style: Stylesheet = {
  selector: "node",
  style: {
    label: "data(label)"
  }
};

export default function CytoscapeComponent({
  elements
}: {
  elements: ElementsDefinition;
}) {
  const ref = React.useRef(null);
  const cy = React.useRef<Cytoscape.Core | null>(null);

  // Setup cytoscape
  React.useEffect(() => {
    if (!ref) {
      return;
    }
    cy.current = Cytoscape({ container: ref.current!, style: [style] });
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
    console.log("updating", elements);
    cy.current.json({ elements });
    cy.current.layout(layout).run();
  }, [cy.current, elements]);

  return <div style={{ height: "1000px" }} ref={ref} />;
}
