import { Typez } from "./schema";
import * as React from "react";
import SelectState from "./SelectState";
import CytoscapeComponent from "./CytoscapeComponent";
import State from "./State";

/**
 * from https://usehooks.com/useDebounce/
 */
function useDebounce<T>(value: T, delay: number): T {
  // State and setters for debounced value

  const [debouncedValue, setDebouncedValue] = React.useState(value);

  React.useEffect(
    () => {
      // Update debounced value after delay

      const handler = setTimeout(() => {
        setDebouncedValue(value);
      }, delay);

      // Cancel the timeout if value changes (also on delay change or unmount)

      // This is how we prevent debounced value from updating if value is changed ...

      // .. within the delay period. Timeout gets cleared and restarted.

      return () => {
        clearTimeout(handler);
      };
    },

    [value, delay] // Only re-call effect if value or delay changes
  );

  return debouncedValue;
}

export default function GraphComponent({ typez }: { typez: Typez }) {
  const [id, setID] = React.useState(typez.states!.initial);
  const [logs, setLogs] = React.useState("");
  const [state, setState] = React.useState(
    () => new State(typez["nodes"]!, id, null)
  );

  const debouncedElements = useDebounce(state.elements, 200);

  React.useEffect(() => {
    setState((oldState) => new State(typez["nodes"]!, id, oldState));
  }, [typez, id]);

  return (
    <div>
      <div
        style={{
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <SelectState
          typez={typez}
          onChange={({ logs, node }) => {
            setID(node);
            setLogs(logs);
          }}
        />
      </div>
      <CytoscapeComponent elements={debouncedElements} />
      <pre>{logs}</pre>
    </div>
  );
}
