/* Project-specific Javascript goes here. */

/**
 * Handles the form submission process by disabling the submit button
 * and showing a loading indicator to prevent multiple submissions.
 *
 * @param {string} formId - The ID of the form element.
 * @param {string} submitButtonId - The ID of the submit button element.
 */
function handleFormSubmission(formId, submitButtonId) {
    // Get the form and submit button elements by their IDs
    /** @type {HTMLFormElement} */
    const form = document.getElementById(formId);

    /** @type {HTMLButtonElement} */
    const submitButton = document.getElementById(submitButtonId);

    // Create a loading indicator element
    /** @type {HTMLDivElement} */
    const loadingIndicator = document.createElement('div');
    loadingIndicator.id = 'loading';
    loadingIndicator.style.display = 'none';
    loadingIndicator.textContent = 'Submitting...';

    // Insert the loading indicator after the "Submit" button
    submitButton.parentNode.insertBefore(loadingIndicator, submitButton.nextSibling);

    // Add an event listener to the form to handle the "submit" event
    form.addEventListener('submit', function(event) {
        // Disable the "Submit" button to prevent multiple submissions
        submitButton.disabled = true;

        // Show the loading indicator to provide feedback to the user
        loadingIndicator.style.display = 'block';
    });
}
