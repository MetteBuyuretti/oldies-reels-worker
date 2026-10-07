import parseTweet from 'twitter-text/dist/esm/parseTweet.js';
const input = document.getElementById('oldies-x-text');
const output = document.getElementById('oldies-x-count');
if (input && output) {
  const refresh = () => {
    const result = parseTweet(input.value);
    output.textContent = `${result.weightedLength}/280 · X twitter-text`;
    output.style.color = result.valid ? '#135e96' : '#b32d2e';
    input.setCustomValidity(result.valid ? '' : 'X metni boş, geçersiz ya da 280 karakter sınırını aşıyor.');
  };
  input.addEventListener('input', refresh);
  refresh();
}
