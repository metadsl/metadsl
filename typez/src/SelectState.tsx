import { Typez } from "./schema";
import * as React from "react";
import Slider from "@material-ui/core/Slider";
import Tooltip from "@material-ui/core/Tooltip";
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

export default function SelectState({
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
