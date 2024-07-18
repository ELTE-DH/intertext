export const getDomain = (matches, property, parts) => {
  const similarities = matches.map(id => id[property] || id[5]).sort();
  const min = similarities[0];
  const max = similarities[matches.length - 1];

  return { elements: splitIntoEqualParts(min, max, parts), min, max };
};

const splitIntoEqualParts = (left, right, parts) => {
  const delta = (right - left) / (parts - 1);
  let result = [];

  while (left < right) {
    result.push(Math.floor(left));
    left += delta;
  }

  result.push(Math.floor(right));

  return result;
};
