// emailCooldown.js

let lastEmailTime = 0;

const getLastEmailTime = () => lastEmailTime;

const updateLastEmailTime = (time) => {
  lastEmailTime = time;
};

export { getLastEmailTime, updateLastEmailTime };