// Simple UI Enhancements

// Confirm delete
document.addEventListener("DOMContentLoaded", function () {

    const deleteButtons = document.querySelectorAll(".btn-delete");

    deleteButtons.forEach(btn => {
        btn.addEventListener("click", function (e) {
            if (!confirm("Are you sure you want to delete?")) {
                e.preventDefault();
            }
        });
    });

});

// Highlight active sidebar link
const links = document.querySelectorAll(".sidebar a");

links.forEach(link => {
    if (link.href === window.location.href) {
        link.style.background = "#1abc9c";
        link.style.color = "white";
    }
});