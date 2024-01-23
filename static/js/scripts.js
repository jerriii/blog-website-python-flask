/*!
 * Start Bootstrap - Clean Blog v6.0.9 (https://startbootstrap.com/theme/clean-blog)
 * Copyright 2013-2023 Start Bootstrap
 * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-clean-blog/blob/master/LICENSE)
 */
window.addEventListener("DOMContentLoaded", () => {
  let scrollPos = 0;
  const mainNav = document.getElementById("mainNav");
  const headerHeight = mainNav.clientHeight;
  window.addEventListener("scroll", function () {
    const currentTop = document.body.getBoundingClientRect().top * -1;
    if (currentTop < scrollPos) {
      // Scrolling Up
      if (currentTop > 0 && mainNav.classList.contains("is-fixed")) {
        mainNav.classList.add("is-visible");
      } else {
        mainNav.classList.remove("is-visible", "is-fixed");
      }
    } else {
      // Scrolling Down
      mainNav.classList.remove(["is-visible"]);
      if (
        currentTop > headerHeight &&
        !mainNav.classList.contains("is-fixed")
      ) {
        mainNav.classList.add("is-fixed");
      }
    }
    scrollPos = currentTop;
  });
});
// JavaScript code for handling search functionality and dropdown
const searchForm = document.getElementById("search-form");
const searchInput = searchForm.querySelector('input[name="query"]');
const searchDropdown = document.getElementById("search-dropdown");

searchInput.addEventListener("input", handleSearchInput);

function handleSearchInput(event) {
  const query = event.target.value;
  if (query.trim() === "") {
    searchDropdown.innerHTML = ""; // Clear dropdown when the search query is empty
  } else {
    // Send AJAX request to the server to get search results
    fetch("/search?q=" + query, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((results) => {
        displaySearchResults(results);
      })
      .catch((error) => {
        console.error("Error fetching search results:", error);
      });
  }
}

function displaySearchResults(results) {
  // Clear previous dropdown content
  searchDropdown.innerHTML = "";

  // Create and append the dropdown items for each search result
  results.forEach((result) => {
    const link = document.createElement("a");
    link.href = "/post/" + result.slug; // Replace with the link to the specific blog post
    link.textContent = result.title;
    searchDropdown.appendChild(link);
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const viewImageBtn = document.getElementById("clickable-image");
  const imageModal = document.getElementById("image-modal");
  const modalImage = document.getElementById("modal-image");
  const closeModalBtn = document.getElementById("close-modal");

  viewImageBtn.addEventListener("click", function () {
    const imgFileName = document.getElementById("img_file").value;
    const imgPath = `/static/assets/img/${imgFileName}`;

    modalImage.src = imgPath;
    imageModal.style.display = "block";
  });

  closeModalBtn.addEventListener("click", function () {
    imageModal.style.display = "none";
  });
});

function previewImage() {
  const fileInput = document.getElementById("img_file");
  const modalImage = document.getElementById("modal-image");

  if (fileInput.files && fileInput.files[0]) {
    const file = fileInput.files[0];
    const reader = new FileReader();

    reader.onload = function (e) {
      modalImage.src = e.target.result;
    };

    reader.readAsDataURL(file);

    const imageModal = document.getElementById("image-modal");
    imageModal.style.display = "flex";

    const closeModalBtn = document.getElementById("close-modal");
    closeModalBtn.addEventListener("click", function () {
      imageModal.style.display = "none";
    });
  }
}
