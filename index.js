// index.js

function trackQuestions() {
  const phyCount = document.getElementById('phy').value;
  const chemCount = document.getElementById('chem').value;
  const mathCount = document.getElementById('math').value;
  const topicsInput = document.getElementById('topics');

  if (phyCount || chemCount || mathCount) {
    const currentDate = new Date().toLocaleDateString();
    const retrospectiveTable = document.getElementById('retrospectiveTable');

    // Create a new row
    const newRow = retrospectiveTable.insertRow(1);

    // Insert cells
    const dateCell = newRow.insertCell(0);
    const phyCell = newRow.insertCell(1);
    const chemCell = newRow.insertCell(2);
    const mathCell = newRow.insertCell(3);
    const topicsCell = newRow.insertCell(4);
    const actionCell = newRow.insertCell(5);

    // Populate cells with data
    dateCell.textContent = currentDate;
    phyCell.textContent = phyCount;
    chemCell.textContent = chemCount;
    mathCell.textContent = mathCount;
    topicsCell.textContent = topicsInput.value;

    // Add Delete button
    const deleteButton = document.createElement('button');
    deleteButton.textContent = 'Delete';
    deleteButton.onclick = function () {
      retrospectiveTable.deleteRow(newRow.rowIndex);
      // Remove data from local storage
      removeEntryFromLocalStorage(currentDate);
    };

    // Append Delete button to the Action cell
    actionCell.appendChild(deleteButton);

    // Save data to local storage
    const data = {
      date: currentDate,
      physics: phyCount,
      chemistry: chemCount,
      mathematics: mathCount,
      topics: topicsInput.value,
    };

    const storedData = JSON.parse(localStorage.getItem('jeeHabitTracker')) || [];
    storedData.push(data);
    localStorage.setItem('jeeHabitTracker', JSON.stringify(storedData));

    // Clear input fields
    document.getElementById('phy').value = '';
    document.getElementById('chem').value = '';
    document.getElementById('math').value = '';
    topicsInput.value = '';
  } else {
    alert('Please enter the number of questions done for at least one subject.');
  }
}

function removeEntryFromLocalStorage(date) {
  const storedData = JSON.parse(localStorage.getItem('jeeHabitTracker')) || [];
  const updatedData = storedData.filter(entry => entry.date !== date);
  localStorage.setItem('jeeHabitTracker', JSON.stringify(updatedData));
}

// Load data from local storage on page load
window.onload = function() {
  const storedData = JSON.parse(localStorage.getItem('jeeHabitTracker')) || [];

  // Populate retrospective table
  const retrospectiveTable = document.getElementById('retrospectiveTable');
  storedData.forEach(entry => {
    const newRow = retrospectiveTable.insertRow(1);

    // Insert cells
    const dateCell = newRow.insertCell(0);
    const phyCell = newRow.insertCell(1);
    const chemCell = newRow.insertCell(2);
    const mathCell = newRow.insertCell(3);
    const topicsCell = newRow.insertCell(4);
    const actionCell = newRow.insertCell(5);

    // Populate cells with data
    dateCell.textContent = entry.date;
    phyCell.textContent = entry.physics;
    chemCell.textContent = entry.chemistry;
    mathCell.textContent = entry.mathematics;
    topicsCell.textContent = entry.topics;

    // Add Delete button
    const deleteButton = document.createElement('button');
    deleteButton.textContent = 'Delete';
    deleteButton.onclick = function () {
      retrospectiveTable.deleteRow(newRow.rowIndex);
      // Remove data from local storage
      removeEntryFromLocalStorage(entry.date);
    };

    // Append Delete button to the Action cell
    actionCell.appendChild(deleteButton);
  });
};
// index.js

// index.js

// ... existing code ...

// index.js

// ... existing code ...

function calculateStatistics() {
  const storedData = JSON.parse(localStorage.getItem('jeeHabitTracker')) || [];
  const totalEntries = storedData.length;

  let totalPhysics = 0;
  let totalChemistry = 0;
  let totalMathematics = 0;

  storedData.forEach(entry => {
    totalPhysics += parseInt(entry.physics) || 0;
    totalChemistry += parseInt(entry.chemistry) || 0;
    totalMathematics += parseInt(entry.mathematics) || 0;
  });

  const totalQuestions = 90;
  const totalQuestionsDone = totalPhysics + totalChemistry + totalMathematics;

  // Percentage Completed Calculation
  const percentageCompleted = ((totalQuestionsDone / (totalEntries * totalQuestions)) * 100).toFixed(2);

  // Rate of Progress Calculation
  const rateOfProgress = (totalQuestionsDone / (totalEntries * totalQuestions)).toFixed(2);

  // Expected Trajectory Calculation
  const expectedTotal = totalEntries * totalQuestions;
  const expectedTrajectory = totalQuestionsDone >= expectedTotal ? 'Progressing' : 'Declining';

  // Display Statistics in the container
  const statisticsContainer = document.getElementById('statisticsContainer');
  statisticsContainer.innerHTML = `
    <p>Total Questions Done: ${totalQuestionsDone}</p>
    <p>Percentage Completed: ${percentageCompleted}%</p>
    <p>Rate of Progress: ${rateOfProgress}</p>
    <p>Expected Trajectory: ${expectedTrajectory}</p>
  `;
}

// ... existing code ...
