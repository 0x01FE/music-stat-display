let all_time_element;
let six_months_element;
let four_weeks_element;
let hours;
let minutes;


function selectButton(id) {
    let button = document.getElementById(id);
    button.classList.add("selectedButton");
}

function resetButtons() {
    let buttonContainer = document.getElementById("TimePeriodSelectionBar");

    for (const child of buttonContainer.children) {
        if (child.tagName === "BUTTON") {
            child.classList.remove("selectedButton");
        }
    }
}

function allTime(id) {
    all_time_element.style.display = "block";
    six_months_element.style.display = "none";
    four_weeks_element.style.display = "none";

    resetButtons();
    selectButton(id);
}

function sixMonths(id) {
    all_time_element.style.display = "none";
    six_months_element.style.display = "block";
    four_weeks_element.style.display = "none";

    resetButtons();
    selectButton(id);
}

function fourWeeks(id) {
    all_time_element.style.display = "none";
    six_months_element.style.display = "none";
    four_weeks_element.style.display = "block";

    resetButtons();
    selectButton(id);
}

addEventListener("DOMContentLoaded", (event) => {
    all_time_element = document.getElementById("all-time");
    six_months_element = document.getElementById("6m");
    four_weeks_element = document.getElementById("4w");

    allTime("b1");
});
