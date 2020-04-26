/**
 * OK the idea here is to be able to represent our types and functions in JSON.
 *
 * Why? Good question, well I think it makes the core system a lot smaller.
 * You can also more easily generate JSON then generate Python code.
 *
 * The idea would be to use this JSON to generate `metadsl` code.
 *
 * This type system is pretty much like System F, because types can take
 * parameters, except it doesn't allow functions to take functions as parameters,
 * only values. Why this restriction? Not sure exactly, I just came to this
 * setup when building from the top down. We actually build an untyped lambda
 * calculus *embedded* in this system, so we use that pass functions to other functions.
 *
 * It's a system for building DSLs, so the functions that you pass around are not first
 * class, they are just data structures that represent functions aka the simply typed
 * lambda calculus. It seems to work!
 *
 * Takes a look at the `metadsl_core` package next to this one, if you wanna see
 * what these things look like in Python land.
 */

/**
 * First we start with some definitions of our type system itself.
 *
 * The idea is these typescript types could be translated into JSON schema
 * with https://github.com/vega/ts-json-schema-generator/
 */

//  TODO: Make typevars keyword mapping instead of arguments

/**
 * A combination of defintions, nodes, and states.
 *
 * The nodes should refer to types in the definitions, and  the states
 * should refer to the nodes.
 */
export type Typez = {
  definitions?: Definitions;
  nodes?: Nodes;
  states?: States;
};

/**
 * Top level definitions can either define type constructor or functions.
 */
type Definitions = {
  // Mapping of names for each  kind/function to the definition
  [name: string]: Kind | Function_;
};

/*
 * This is a "kind" because it is a type of a type, or a type constructor
 */
type Kind = {
  // names of the type parameters
  params?: Array<string>;
};

/**
 * A definition for a function. Everything that would be a method in python
 * is defined here as just a function, with the idea being that if it is named
 * like `<type name>.<method name>` and its first argument takes in the type,
 * then it is a method.
 */

type Function_ = {
  // name of the type variables
  type_params?: Array<string>;
  // argument types
  params: Array<[string, Type]>;
  // variable argument type, if null then variable args are not allowed
  rest_param?: [string, Type] | null;
  // return type
  return_: Type;
};

/**
 * A type we use  to define a function.
 */
type Type = TypeParameter | DeclaredType | ExternalType;

type TypeParameter = {
  param: string;
};

type DeclaredType = {
  type: string;
  // mapping of type param names to their types
  params?: { [name: string]: Type };
};

type ExternalType = {
  type: string;
  repr: string;
};

/**
 * A mapping of node IDs to the functions
 */
export type Nodes = Array<CallNode | PrimitiveNode>;

export type CallNode = {
  id: string;
  function: string;
  type_params?: { [name: string]: TypeInstance };
  // An array of the ids of the argument nodes
  args?: Array<string>;
  // A mapping of keyward name to node ID
  kwargs?: { [name: string]: string };
};

/**
 * A primitive node that represents some type in  the host language
 */
type PrimitiveNode = { id: string; type: string; repr: string };

/**
 * A type that is passed into a function to set one of its  type
 */
type TypeInstance = DeclaredTypeInstance | ExternalTypeInstance;
type DeclaredTypeInstance = {
  type: string;
  params?: { [name: string]: TypeInstance };
};
type ExternalTypeInstance = {
  repr: string;
};
/**
 * A sequence of the states the expression is in.
 */
type States = {
  // the initial node
  initial: string;
  // An array of subsequent states
  states?: Array<State>;
};

type State = {
  // The node for this state
  node: string;
  // The name of the rule that was used to get to this state
  rule: string;
  // An optional label to be shown to the user, to highlight this state
  label?: string;
  // Logs  for this state
  logs: string;
};

/**
 * Examples
 */

// const Natural: Definitions = {
//   "Natural": {},
//   "Natural.__add__": {
//     params: [["left", {type: "Natural"}], ["right", {type: "Natural"}]],
//     return_: {type: "Natural"}
//   },
//   "Vec": ["Item"],
//   "Vec.__getitem__": {
//     type
//   }
// };

// const Vec: Definitions = {

//   "Vec": ["T"] }
//   {
//     function: "Vec.__getitem__",
//     type_params: ["T"],
//     params: [["self", { param: "T" }], ["index", { type: "Nat" }]],
//     return: { param: "T" }
//   }
// ];
