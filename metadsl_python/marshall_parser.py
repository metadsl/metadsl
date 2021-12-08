from lark import Lark

marshall_parser = Lark(
    """
    object:
        | "T" -> true
        | "F" -> false
        | "N" -> none
        | "S" -> stop_iteration
        | "." -> ellipsis
        | "\xe9" -> int
    """,
    start="object",
)
