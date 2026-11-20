// PROTOTYPE: the record form keeps the node type in data.type; the view reads kind (the document form).
export const toViewGraph = (g) => ({ nodes: g.nodes.map((n) => ({ ...n, kind: n.data?.type === 'data' ? 'data' : 'process' })), edges: g.edges });
