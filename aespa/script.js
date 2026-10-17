const questions = [
  { text: "Your friends are planning a night out. What's your role?", answers: [
    ["I set the vibe and make sure everyone feels included.", "karina"], ["I'm already on the aux with a perfectly curated playlist.", "giselle"], ["I bring the bold idea nobody saw coming.", "ningning"], ["I keep it spontaneous and turn it into an adventure.", "winter"]
  ]},
  { text: "Pick the energy you want to bring into a room.", answers: [
    ["Quiet confidence that draws people in.", "winter"], ["Warm, magnetic main-character energy.", "karina"], ["Playful creativity with a little edge.", "giselle"], ["Fearless, expressive, impossible to ignore.", "ningning"]
  ]},
  { text: "Your perfect creative project would be…", answers: [
    ["A cinematic concept with a whole world behind it.", "karina"], ["A clever track with unexpected twists.", "giselle"], ["A powerful performance that gives everyone chills.", "ningning"], ["A clean, cool design with one unforgettable detail.", "winter"]
  ]},
  { text: "When a challenge shows up, you…", answers: [
    ["Stay cool, focus, and handle it one step at a time.", "winter"], ["Bring the team together and lead the way.", "karina"], ["Trust your instincts and go all in.", "ningning"], ["Find a fresh angle and make it your own.", "giselle"]
  ]},
  { text: "Choose a word that feels most like you.", answers: [
    ["Commanding", "karina"], ["Original", "giselle"], ["Radiant", "ningning"], ["Composed", "winter"]
  ]}
];
const members = {
  karina: { name: "Karina", mark: "K", trait: "The magnetic leader", copy: "You have a natural presence that makes people feel at ease and ready to follow your lead. Thoughtful, driven, and quietly powerful, you bring the whole team into focus.", note: "YOUR æ-KEYWORD / PRESENCE" },
  giselle: { name: "Giselle", mark: "G", trait: "The original creative", copy: "Quick-witted and full of ideas, you make every moment feel a little more interesting. You know your own mind, bring your own flavor, and make creativity look effortless.", note: "YOUR æ-KEYWORD / ORIGINALITY" },
  winter: { name: "Winter", mark: "W", trait: "The cool perfectionist", copy: "Calm, precise, and full of surprises, you have a steady confidence that speaks for itself. You notice the details, keep your cool, and shine when it counts.", note: "YOUR æ-KEYWORD / CLARITY" },
  ningning: { name: "Ningning", mark: "N", trait: "The fearless performer", copy: "Expressive and full of life, you bring big energy wherever you go. You trust your talent, wear your heart openly, and make sure nobody forgets the moment.", note: "YOUR æ-KEYWORD / SPARK" }
};
let current = 0;
const scores = { karina: 0, giselle: 0, winter: 0, ningning: 0 };
const content = document.querySelector('#quiz-content');
const fill = document.querySelector('#progress-fill');
const label = document.querySelector('#step-label');
const count = document.querySelector('#progress-count');
function renderQuestion() {
  const q = questions[current];
  const n = String(current + 1).padStart(2, '0');
  label.textContent = `QUESTION ${n} / ${String(questions.length).padStart(2, '0')}`;
  count.innerHTML = `${n} <b>—</b> ${String(questions.length).padStart(2, '0')}`;
  fill.style.width = `${((current + 1) / questions.length) * 100}%`;
  content.innerHTML = `<p class="question-kicker">${n} / YOUR INSTINCTS</p><h2 class="question">${q.text}</h2><div class="options">${q.answers.map(([text], i) => `<button class="option" data-answer="${i}"><span class="option-index">0${i + 1}</span><span>${text}</span><span class="option-arrow">↗</span></button>`).join('')}</div>`;
  content.querySelectorAll('.option').forEach(button => button.addEventListener('click', () => choose(Number(button.dataset.answer))));
}
function choose(index) {
  scores[questions[current].answers[index][1]]++;
  current++;
  if (current < questions.length) renderQuestion(); else renderResult();
}
function renderResult() {
  const highest = Math.max(...Object.values(scores));
  const winner = Object.keys(scores).find(key => scores[key] === highest);
  const member = members[winner];
  label.textContent = 'SCAN COMPLETE / 05';
  count.innerHTML = '05 <b>—</b> 05';
  fill.style.width = '100%';
  content.innerHTML = `<div class="result"><div class="result-symbol">${member.mark}</div><p class="result-tag">YOUR æ-MATCH IS</p><h2>${member.name}</h2><p class="question-kicker">${member.trait.toUpperCase()}</p><p class="result-copy">${member.copy}</p><p class="result-note">${member.note}</p><button class="restart">↻ &nbsp; TAKE THE QUIZ AGAIN</button></div>`;
  content.querySelector('.restart').addEventListener('click', restart);
}
function restart() {
  current = 0;
  Object.keys(scores).forEach(key => scores[key] = 0);
  renderQuestion();
}
renderQuestion();
