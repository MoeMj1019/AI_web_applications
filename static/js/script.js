function clearSearch() {
    document.getElementById("searchInput").value = "";
    document.getElementById("clearButton").style.visibility = "hidden"; // Hide button when input is cleared
}

function showClearButton() {
    if (document.getElementById("searchInput").value.length > 0) {
        document.getElementById("clearButton").style.visibility = "visible";
    } else {
        document.getElementById("clearButton").style.visibility = "hidden";
    }
}