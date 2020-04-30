import { Typez } from "./schema";
import * as React from "react";
import Slider from "@material-ui/core/Slider";
import Tooltip from "@material-ui/core/Tooltip";
import Input from "@material-ui/core/Input";
import PopperJs from "popper.js";

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
        popperRef,
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

export default function SelectState({
  typez: { states },
  onChange,
}: {
  typez: Typez;
  onChange: (options: { node: string; logs: string }) => void;
}) {
  // selected index, from the right
  const [selected, setSelected] = React.useState<number>(0);
  const n = states?.states?.length || 0;
  const i = n - selected;
  React.useEffect(() => {
    if (i === 0) {
      onChange({ node: states!.initial, logs: "" });
    } else {
      const { node, logs } = states!.states![i - 1]!;
      onChange({ node, logs });
    }
  }, [states, selected]);

  return (
    <div style={{ display: "flex" }}>
      <Input
        value={i}
        margin="dense"
        type="number"
        onChange={(event) => setSelected(n - Number(event.target.value))}
        inputProps={{
          step: 1,
          min: 0,
          max: n,
          type: "number",
        }}
      />
      <Slider
        style={{ marginLeft: 60, marginRight: 60, marginTop: 8 }}
        ValueLabelComponent={({ children, open, value }) => (
          <ValueLabelComponent
            children={children}
            open={open}
            value={value === 0 ? "initial" : states!.states![value - 1].rule}
          />
        )}
        step={1}
        valueLabelDisplay="on"
        value={i}
        max={n}
        onChange={(_, newValue) => setSelected(n - (newValue as any))}
        marks={[
          { value: 0, label: "initial" },
          ...(states?.states ?? []).map(({ label }, idx) => ({
            value: idx + 1,
            label,
          })),
        ]}
      />
    </div>
  );
}
