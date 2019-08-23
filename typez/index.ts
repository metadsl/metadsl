// Polymorphic type
type Kind = {
  type: string;
  // names of the type parameters
  params: Array<string>;
};

type TypeVariable<T extends string> = {
  param: T;
};
type TypeType<T extends string> = {
  type: string;
  params: Array<Type<T>>;
};
type Type<T extends string> = TypeVariable<T> | TypeType<T>;

type Function_<T extends string> = {
  function: string;
  // name of the type variables
  type_params: Array<T>;
  // arguments
  params: Array<{ name: string; type: Type<T> }>;
  return: Type<T>;
};

type Definitions = Array<Function_<any> | Kind>;

// Now for some examples..

// Untyped lambda calculus anyone?
const Abstraction: Definitions = [
  {
    type: "Abstraction",
    params: ["ARG", "RET"]
  },
  {
    function: "Abstraction.create",
    type_params: ["ARG", "RET"],
    params: [
      { name: "var", type: { param: "ARG" } },
      { name: "body", type: { param: "RET" } }
    ],
    return: {
      type: "Abstraction",
      params: [{ param: "ARG" }, { param: "RET" }]
    }
  },
  {
    function: "Abstraction.__call__",
    type_params: ["ARG", "RET"],
    params: [
      {
        name: "self",
        type: {
          type: "Abstraction",
          params: [{ param: "ARG" }, { param: "RET" }]
        }
      },
      {
        name: "arg",
        type: { param: "ARG" }
      }
    ],
    return: { param: "RET" }
  }
];

const Maybe: Definitions = [
  {
    type: "Maybe",
    params: ["T"]
  },
  {
    function: "Maybe.nothing",
    type_params: ["T"],
    params: [],
    return: { type: "Maybe", params: [{ param: "T" }] }
  },
  {
    function: "Maybe.just",
    type_params: ["T"],
    params: [{ name: "value", type: { param: "T" } }],
    return: { type: "Maybe", params: [{ param: "T" }] }
  },
  {
    function: "Maybe.match",
    type_params: ["ARG", "RET"],
    params: [
      { name: "self", type: { type: "Maybe", params: [{ param: "RET" }] } },
      { name: "nothing", type: { param: "RET" } },
      {
        name: "just",
        type: {
          type: "Abstraction",
          params: [{ param: "ARG" }, { param: "RET" }]
        }
      }
    ],
    return: { param: "RET" }
  }
];
