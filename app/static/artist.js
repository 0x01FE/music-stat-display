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
    let buttonContainer = document.getElementById("ArtistPeriodSelectionBar");

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

    hours.textContent = times["overall"][0];
    minutes.textContent = times["overall"][1];

    resetButtons();
    selectButton(id);
}

function sixMonths(id) {
    all_time_element.style.display = "none";
    six_months_element.style.display = "block";
    four_weeks_element.style.display = "none";

    hours.textContent = times["six_months"][0];
    minutes.textContent = times["six_months"][1];

    resetButtons();
    selectButton(id);
}

function fourWeeks(id) {
    all_time_element.style.display = "none";
    six_months_element.style.display = "none";
    four_weeks_element.style.display = "block";

    hours.textContent = times["one_month"][0];
    minutes.textContent = times["one_month"][1];

    resetButtons();
    selectButton(id);
}

addEventListener("DOMContentLoaded", (event) => {
    all_time_element = document.getElementById("all-time");
    six_months_element = document.getElementById("6m");
    four_weeks_element = document.getElementById("4w");

    hours = document.getElementById("hours");
    minutes = document.getElementById("minutes");

    selectButton("b1");
});
