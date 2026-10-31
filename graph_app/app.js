// The page of the Graph app (N-5). T-01: open a graph or a library entry from a JSON file and draw it (REQ-GA-001).
// Reading and saving through IF-104 follow in the later tasks of the node plan.
import { graphOf, svgMarkup } from './graph-view.js';

const view = document.getElementById('view');
const status = document.getElementById('status');

function show(entry, name) {
  try {
    const graph = graphOf(entry);
    view.innerHTML = svgMarkup(graph);  // the markup escapes every id
    status.textContent = `${name}: ${graph.nodes.length} nodes, ${graph.edges.length} edges`;
  } catch (error) {
    view.textContent = '';
    status.textContent = `${name}: ${error.message}`;
  }
}

document.getElementById('file').addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    show(JSON.parse(await file.text()), file.name);
  } catch (error) {
    status.textContent = `${file.name}: not JSON (${error.message})`;
  }
});
