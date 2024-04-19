var current_graph_display = "DailyTimeGraph";
var graphs = null;

function draw_graphs() {

    let graph_select = document.getElementById("graph-select");
    let current_graph_display = graph_select.value;

    for (const child of graphs.children)
    {
        if (child.id === current_graph_display)
        {
            child.style.display = "block";
        }
        else {
            child.style.display = "none";
        }
    }


};

addEventListener("DOMContentLoaded", (event) => {
    graphs = document.getElementById("graphs");
});
