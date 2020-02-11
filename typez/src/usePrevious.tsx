import * as React from "react";

/**
 * https://reactjs.org/docs/hooks-faq.html#how-to-get-the-previous-props-or-state
 */
export default function usePrevious<T>(value: T): T | undefined {
  const ref = React.useRef<undefined | T>();
  React.useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}
