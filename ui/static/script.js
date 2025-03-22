const socket = io();

// **Toggle Feature Function**
function toggleFeature(feature, button) {
    socket.emit("toggle_feature", { feature: feature });

    // Toggle Button Text & Color
    let currentText = button.innerText;
    if (currentText.includes("ON")) {
        button.innerText = currentText.replace("ON", "OFF");
        button.style.backgroundColor = "#666";  // Gray OFF
    } else {
        button.innerText = currentText.replace("OFF", "ON");
        button.style.backgroundColor = "#E22DA1";  // Pink ON
    }
}

// **Audio Button**
document.getElementById("audio-btn").addEventListener("click", function() {
    toggleFeature("audio", this);
});

// **Screen Button**
document.getElementById("screen-btn").addEventListener("click", function() {
    toggleFeature("screen", this);
});

// **Mouse Button - Toggles Heaters**
document.getElementById("mouse-btn").addEventListener("click", function() {
    toggleFeature("mouse", this);
    
    let heaterDiv = document.getElementById("heater-controls");
    heaterDiv.style.display = heaterDiv.style.display === "none" ? "block" : "none";
});

// **Heater Buttons**
document.getElementById("heater-1").addEventListener("click", function() {
    toggleFeature("heater1", this);
});
document.getElementById("heater-2").addEventListener("click", function() {
    toggleFeature("heater2", this);
});
document.getElementById("heater-3").addEventListener("click", function() {
    toggleFeature("heater3", this);
});