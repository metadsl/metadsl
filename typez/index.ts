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

/**
 * Top level definitions can either define type constructor or functions.
 */
type Definitions = Array<Function_<any> | Kind>;

/*
 * This is a "kind" because it is a type of a type, or a type constructor
 */
type Kind = {
  // label for for the function
  type: string;
  // names of the type parameters
  params: Array<string>;
};

/**
 * A definition for a function. Everything that would be a method in python
 * is defined here as just a function, with the idea being that if it is named
 * like `<type name>.<method name>` and its first argument takes in the type,
 * then it is a method.
 *
 * We don't really need this T paramterization here, but it helps
 * us verify, with typescript, that the params can only use type params
 * defined in the type params, not other strings. I doubt it will translate
 * to JSON schema, but it's nice in here.
 */

type Function_<T extends string> = {
  function: string;
  // name of the type variables
  type_params: Array<T>;
  // arguments
  params: Array<{ name: string; type: Type<T> }>;
  return: Type<T>;
};

/**
 * This is reference to an instantiated type, either one of the type variables
 * or a predifined type
 */
type Type<T extends string> = TypeVariable<T> | TypeType<T>;

type TypeVariable<T extends string> = {
  param: T;
};
type TypeType<T extends string> = {
  type: string;
  params: Array<Type<T>>;
};

/**
 * Now that we defined our language, we can become writing types and functions in it!
 *
 * Let's start with the untyped lamba calculus.
 */
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

/**
 * Using that, we can create a definition for a "Maybe" type...
 */
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
