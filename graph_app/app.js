// The page of the Graph app (N-5). T-01: open a graph, a library entry or a stored record from a JSON file and draw it with vis-network
// (REQ-GA-001, D-124). Reading and saving through IF-104 follow in the later tasks of the node plan; nothing here leaves the page.
import { graphsOf, visData, visOptions } from './graph-view.js';

const view = document.getElementById('view');
const status = document.getElementById('status');
const detail = document.getElementById('detail');
const pick = document.getElementById('pick');
let network = null;
let shown = [];

/** the colors of the page's style (light or dark), since vis-network draws on a canvas and does not read CSS */
function colors() {
  const style = getComputedStyle(document.documentElement);
  const value = (name) => style.getPropertyValue(name).trim();
  return { data: value('--data'), process: value('--process'), line: value('--line'), text: value('--fg') };
}

function draw(fileName, { name, graph }) {
  const { nodes, edges, problems } = visData(graph);
  network?.destroy();
  network = new vis.Network(view, { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }, visOptions(colors()));
  network.on('click', ({ nodes: [nodeId], edges: [edgeId] }) => {
    const nodeEntry = nodeId === undefined ? undefined : graph.nodes.find((node) => node.id === nodeId);
    const edgeEntry = edgeId === undefined ? undefined : graph.edges[Number(edgeId.slice(1))];
    const entry = nodeEntry ?? edgeEntry;
    detail.textContent = entry === undefined ? '' : JSON.stringify(entry, null, 2);   // text, never markup
  });
  const counts = `${nodes.length} nodes, ${edges.length} edges`;
  status.textContent = `${fileName} (${name}): ${counts}${problems.length ? `; not drawn: ${problems.join('; ')}` : ''}`;
  detail.textContent = '';
}

function show(entry, fileName) {
  shown = graphsOf(entry);
  pick.replaceChildren(...shown.map(({ name }, index) => new Option(name, String(index))));
  pick.parentElement.hidden = shown.length < 2;
  pick.onchange = () => draw(fileName, shown[Number(pick.value)]);
  draw(fileName, shown[0]);
}

document.getElementById('file').addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    show(JSON.parse(await file.text()), file.name);
  } catch (error) {
    network?.destroy();
    network = null;
    status.textContent = `${file.name}: ${error.message}`;
  }
});
