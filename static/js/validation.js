//Show password icon
const passwordInput = document.getElementById("password");
const showPasswordToggle = document.getElementById("showPasswordToggle");
showPasswordToggle.addEventListener("click", function () {
  if (passwordInput.type === "password") {
    passwordInput.type = "text";
  } else {
    passwordInput.type = "password";
  }
});

//phone number validation
const phoneInput = document.getElementById("phone");

phoneInput.addEventListener("input", function (event) {
  event.target.value = event.target.value.replace(/\D/g, "");
});

//email validation
const emailInput = document.getElementById("email");
const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

emailInput.addEventListener("input", function (event) {
  const email = event.target.value;
  const isValid = emailPattern.test(email);

  if (!isValid) {
    emailInput.setCustomValidity(
      "Please enter a valid email address (someone@example.com)."
    );
  } else {
    emailInput.setCustomValidity("");
  }
});

const usernameInput = document.getElementById("username");

usernameInput.addEventListener("input", () => {
  let inputText = usernameInput.value.trim();

  if (/^[a-zA-Z]/.test(inputText)) {
    usernameInput.value =
      inputText.charAt(0).toUpperCase() + inputText.slice(1);
  } else {
    usernameInput.value = "";
    console.log("Name should start with a letter.");
  }
});
