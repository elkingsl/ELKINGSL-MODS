fetch('data/mods.json')
  .then(response => response.json())
  .then(data => {
    const container = document.getElementById('mods-container');

    data.forEach(mod => {
      const card = document.createElement('div');
      card.className = 'mod-card';

      card.innerHTML = `
        <img src="${mod.image}" alt="${mod.name}">
        <h2>${mod.name}</h2>
        <p>${mod.description}</p>
        <p><strong>Version:</strong> ${mod.version}</p>
        <a href="${mod.download}" download>Download</a>
      `;

      container.appendChild(card);
    });
  })
  .catch(error => console.error('Error loading mods:', error));