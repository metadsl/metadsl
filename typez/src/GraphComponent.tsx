import { Typez } from "./schema";
import * as React from "react";
import SelectState from "./SelectState";
import CytoscapeComponent from "./CytoscapeComponent";
import State from "./State";

export default function GraphComponent({ typez }: { typez: Typez }) {
  const [id, setID] = React.useState(typez.states!.initial);
  const [state, setState] = React.useState(
    () => new State(typez["nodes"]!, id, null)
  );

  React.useEffect(() => {
    setState(oldState => new State(typez["nodes"]!, id, oldState));
  }, [typez, id]);
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
      <CytoscapeComponent elements={state.elements} />
    </div>
  );
}
