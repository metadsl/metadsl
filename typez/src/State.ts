import { ElementsDefinition } from "cytoscape";
import { Nodes, CallNode } from "./schema";
import getSafe from "./getSafe";

type Children = Map<string | number, string>;
type Parents = { id: string; index: number | string }[];

function* nodeChildren({
  args,
  kwargs
}: CallNode): Generator<{ index: string | number; childID: string }> {
  if (args) {
    for (const [index, childID] of args.entries()) {
      yield { index, childID };
    }
  }
  if (kwargs) {
    for (const [index, childID] of Object.entries(kwargs)) {
      yield { index, childID };
    }
  }
}
const PARENT_OF_ROOT_ID = "parent-of-root-id";
const PARENT_OF_ROOT_ELEMENT_ID = "parent-of-root-element-id";

export default class State {
  public readonly elements: ElementsDefinition = { nodes: [], edges: [] };

  private nextNewID: number;
  // Mapping of parent element ID to list of children element ID
  private readonly parentElementIDToChildrenElementIDs = new Map<
    string,
    Children
  >();
  // Mapping of IDs to the new element IDs we generate for them
  private readonly idToElementID = new Map<string, string>([
    [PARENT_OF_ROOT_ID, PARENT_OF_ROOT_ELEMENT_ID]
  ]);

  private readonly elementIDs = new Set();
  // mapping of ids to the ID of each parent and the index of the child
  private readonly idToParents: Map<string, Parents>;
  /**
   * Creates a new state of elements, based on the old state, the new nodes, and the new root ID
   */
  constructor(nodes: Nodes, rootID: string, private previous: State | null) {
    this.nextNewID = this.previous?.nextNewID ?? 0;

    // Set parent of root id to be fixed node so we can track it's previous element ID
    this.idToParents = new Map([
      [rootID, [{ id: PARENT_OF_ROOT_ID, index: 0 }]]
    ]);

    /**
     * Nodes are sorted in Topological order so we can iterate through them until we get the the root ID
     */
    const IDsToProcess = new Set([rootID]);
    // Reverse so that in topo order with root at the front instead of back
    for (const node of [...nodes].reverse()) {
      const { id } = node;
      if (!IDsToProcess.has(id)) {
        continue;
      }
      IDsToProcess.delete(id);
      const elementID = this.computeElementID(id);

      if (this.elementIDs.has(elementID)) {
        throw new Error();
      }
      this.idToElementID.set(id, elementID);
      this.elementIDs.add(elementID);
      let label: string;
      if ("repr" in node) {
        label = node.repr;
      } else {
        label = node.function;
        for (const { index, childID } of nodeChildren(node)) {
          IDsToProcess.add(childID);
          this.recordParent({ childID, parentID: id, index });
        }
      }
      this.elements.nodes.push({ data: { id: elementID, label } });

      for (const { id: parentID, index } of getSafe(this.idToParents, id)) {
        const parentElementID = getSafe(this.idToElementID, parentID);
        const children: Children = getSafe(
          this.parentElementIDToChildrenElementIDs,
          parentElementID,
          new Map()
        );
        children.set(index, elementID);
        if (parentID === PARENT_OF_ROOT_ID) {
          // Don't add actual edge for root of parent, just for bookeeping so
          // we can preserve its element ID
          continue;
        }
        this.elements.edges.push({
          data: {
            source: parentElementID,
            id: `${parentElementID}.${index}`,
            target: elementID
          }
        });
      }
    }
    if (IDsToProcess.size !== 0) {
      throw new Error();
    }
    // Remove so it can be GCed
    this.previous = null;
  }

  private recordParent({
    childID,
    parentID,
    index
  }: {
    childID: string;
    parentID: string;
    index: string | number;
  }): void {
    let parents: Parents;
    if (this.idToParents.has(childID)) {
      parents = this.idToParents.get(childID)!;
    } else {
      parents = [];
      this.idToParents.set(childID, parents);
    }
    parents.push({ id: parentID, index });
  }

  /**
   * Computes the new element ID with a heuristic meant
   * to make the transitions as natural as possible by
   * having preserving the IDs of similarily places items
   * when moving between graphs.
   *
   * We compute the new ID of a node by looking in this order, choosing the first that hasn't
   * been given out yet:
   *
   * 1. The element ID previously assigned to this ID (hash)
   * 2. Any of the previously assigned element IDs to this ID by its parents, related
   *    to this child index. If multiple match, choice is arbitrary.
   * 3. Make up a new ID (which has never globally been assigned) and give it to this node.
   */
  private computeElementID(id: string): string {
    return (
      this.newElementIDOrNull(this.previous?.idToElementID.get(id)) ??
      this.newElementIDOrNull(this.computeElementIDByParents(id)) ??
      (this.nextNewID++).toString()
    );
  }

  private newElementIDOrNull(
    elementID: string | undefined | null
  ): string | null | undefined {
    if (this.elementIDs.has(elementID)) {
      return null;
    }
    return elementID;
  }

  private computeElementIDByParents(id: string): string | null {
    const parents = getSafe(this.idToParents, id);
    // Mapping of previous ID to count that it was assigned
    const previousElementIDs = new Map<string, number>();

    for (const { id: parentID, index } of parents) {
      const parentElementID = getSafe(this.idToElementID, parentID);
      const previousElementID = this.previous?.parentElementIDToChildrenElementIDs
        .get(parentElementID)
        ?.get(index);
      if (previousElementID) {
        previousElementIDs.set(
          previousElementID,
          (previousElementIDs.get(previousElementID) ?? 0) + 1
        );
      }
    }
    // Compute top occurance of previous ID
    let topPreviouslyAssigned: [null | string, number] = [null, 0];
    previousElementIDs.forEach((count, elementID) => {
      if (count > topPreviouslyAssigned[1]) {
        topPreviouslyAssigned = [elementID, count];
      }
    });
    return topPreviouslyAssigned[0];
  }
}
