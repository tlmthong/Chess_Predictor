window.onload = function () {
  document
    .getElementById('predictButton')
    .addEventListener('click', main)
}
function handleModeChange (radio) {
  console.log('Selected mode:', radio.value)
}
function handleStartChange (radio) {
  console.log('Selected start:', radio.value)
}
function predictOutcome (usernameWhite, usernameBlack, choicePlayer) {
  console.log('Button clicked!')
  let checkedRadio = document.querySelector('input[name="mode"]:checked')
  let choice_wdl = checkedRadio ? checkedRadio.value : null
  console.log('Selected choice:', choice_wdl)
  let choice
  if (choice_wdl === 'WL') {
    choice = 2
  } else {
    choice = 1
  }
  console.log('Choice for prediction:', choice)
  // let usernameWhite = document.getElementById('username_white').value
  // let usernameBlack = document.getElementById('username_black').value
  let eco = document.getElementById('eco').value
  let time = parseInt(document.getElementById('time').value)
  let increment = parseInt(document.getElementById('increment').value)
  // let playerBettingRadio = document.querySelector('input[start="mode"]:checked')
  // let playerBetting = playerBettingRadio ? playerBettingRadio.value : null
  // if (playerBetting === 'white') {
  //   choicePlayer = 1
  // } else if (playerBetting === 'black') {
  //   choicePlayer = 0
  // } else {
  //   choicePlayer = null
  // }
  console.log('Player betting choice:', choicePlayer)

  return fetch('/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      choice,
      usernameWhite,
      usernameBlack,
      eco,
      time,
      increment,
      choicePlayer
    })
  })
    .then(res => res.json()) // <-- This returns the JSON data
    .then(data => {
      console.log(data)
      return data.probability // <-- This returns the probability value
    })
    .catch(err => {
      console.error('Prediction failed:', err)
      alert('Something went wrong.')
      return undefined
    })
}
async function calculateBestWin (threshold, n) {
  let usernameWhite = document.getElementById('username_white').value
  let usernameBlack = document.getElementById('username_black').value
  let playerBettingRadio = document.querySelector('input[name="start"]:checked')
  let startchoice = playerBettingRadio ? playerBettingRadio.value : null

  console.log('Player betting choice:', startchoice)
  let x1, x2;
  if (startchoice == 'white') {
    x1 = await predictOutcome(usernameWhite, usernameBlack, 1) // white
    console.log('x1:', x1)
    x2 = await predictOutcome(usernameBlack, usernameWhite, 0)
    console.log('x2:', x2)
    let sum_pX = 0;
    for (let i = 1; i < n; i++) {
      let pX = bernouli_process(i, n, x1, x2)
      console.log('Sum of Bernoulli process probabilities:', sum_pX)
      console.log('Bernoulli process probability:', pX)
      sum_pX += pX;
      if (sum_pX > threshold) {
        return i
      }
    }
    return n 
  } else if (startchoice == 'black') {
    x2 = await predictOutcome(usernameWhite, usernameBlack, 0) // black
    console.log('x2:', x2)
    x1 = await predictOutcome(usernameBlack, usernameWhite, 1)
    console.log('x1:', x1)
    let sum_pX = 0;
    for (let i = 1; i < n; i++) {
      let pX = bernouli_process(i, n, x1, x2)
      sum_pX += pX
      console.log('Sum of Bernoulli process probabilities:', sum_pX)
      console.log('Bernoulli process probability:', pX)
      if (sum_pX > threshold) {
        return i
      }
    }
    return n
  }
}




function binomialCoefficient(n, k) {
  if (k < 0 || k > n) return 0;
  if (k === 0 || k === n) return 1;
  k = Math.min(k, n - k); // take advantage of symmetry
  let c = 1;
  for (let i = 0; i < k; i++) {
    c = c * (n - i) / (i + 1);
  }
  return c;
}

function bernouli_process(k, n, x1, x2) {
  const w = Math.ceil(n / 2);   // number of white games
  const b = Math.floor(n / 2);  // number of black games

  let prob = 0;
  const iMin = Math.max(0, k - b);
  const iMax = Math.min(k, w);

  for (let i = iMin; i <= iMax; i++) {
    const winsWhite = i;
    const winsBlack = k - i;

    const pWhite = binomialCoefficient(w, winsWhite) * Math.pow(x1, winsWhite) * Math.pow(1 - x1, w - winsWhite);
    const pBlack = binomialCoefficient(b, winsBlack) * Math.pow(x2, winsBlack) * Math.pow(1 - x2, b - winsBlack);

    prob += pWhite * pBlack;
  }

  return prob;
}


async function main() {
  let confident = 1 -  document.getElementById('confident').value
  if (!confident) confident = 0.5;
  let num_game = document.getElementById('num_game').value
  console.log("about to calculate")
  let number_win_needed = await calculateBestWin(confident, num_game);
  console.log(number_win_needed)
  let rest_game = num_game - number_win_needed
  alert("Bet at (Your Friend - You): "+ "("+ rest_game+"-"+number_win_needed+")")
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}