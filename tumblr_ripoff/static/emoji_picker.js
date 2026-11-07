const emojiCategories = {
    Smileys: [
        "😀 😃 😄 😁 😆 😅 😂 🙂 🙃 🫠 😉 😊 😇 🥰 😍 🤩 😘 😗 ☺️ 😚 😙 🥲",
        "😋 😛 😜 🤪 😝 🤑 🤗 🤭 🫢 🫣 🤫 🤔 🫡 🤐 🤨 😐 😑 😶 🫥 😶‍🌫️",
        "😏 😒 🙄 😬 😮‍💨 🤥 🫨 🙂‍↔️ 🙂‍↕️ 😌 😔 😪 🤤 😴 🥱 😷 🤒 🤕",
        "🤢 🤮 🤧 🥵 🥶 🥴 😵 😵‍💫 🤯 🤠 🥳 🥸 😎 🤓 🧐 😕 🫤 😟 🙁",
        "☹️ 😮 😯 😲 😳 🥺 🥹 😦 😧 😨 😰 😥 😢 😭 😱 😖 😣 😞 😓",
        "😩 😫 🥱 😤 😡 😠 🤬 😈 👿 💀 ☠️ 💩 🤡 👹 👺 👻 👽 👾 🤖 🎃",
        "😺 😸 😹 😻 😼 😽 🙀 😿 😾"
    ],
    People: [
        "👋 🤚 🖐️ ✋ 🖖 🫱 🫲 🫳 🫴 👌 🤌 🤏 ✌️ 🤞 🫰 🤟 🤘 🤙 👈 👉",
        "👆 🖕 👇 ☝️ 🫵 👍 👎 ✊ 👊 🤛 🤜 👏 🙌 🫶 👐 🤲 🤝 🙏 ✍️ 💅",
        "🤳 💪 🦾 🦿 🦵 🦶 👂 🦻 👃 🧠 🫀 🫁 🦷 🦴 👀 👁️ 👅 👄 🫦",
        "👋🏻 👋🏼 👋🏽 👋🏾 👋🏿 👍🏻 👍🏼 👍🏽 👍🏾 👍🏿 👎🏻 👎🏼 👎🏽 👎🏾 👎🏿",
        "👏🏻 👏🏼 👏🏽 👏🏾 👏🏿 🙌🏻 🙌🏼 🙌🏽 🙌🏾 🙌🏿 🙏🏻 🙏🏼 🙏🏽 🙏🏾 🙏🏿",
        "💪🏻 💪🏼 💪🏽 💪🏾 💪🏿 🤝🏻 🤝🏼 🤝🏽 🤝🏾 🤝🏿",
        "👶 🧒 👦 👧 🧑 👨 👩 🧔 🧔‍♂️ 🧔‍♀️ 👱 👱‍♂️ 👱‍♀️ 🧓 👴 👵",
        "👶🏻 👶🏼 👶🏽 👶🏾 👶🏿 🧑🏻 🧑🏼 🧑🏽 🧑🏾 🧑🏿",
        "👨🏻 👨🏼 👨🏽 👨🏾 👨🏿 👩🏻 👩🏼 👩🏽 👩🏾 👩🏿",
        "🙍 🙎 🙅 🙆 💁 🙋 🧏 🙇 🤦 🤷 👮 🕵️ 💂 🥷 👷 🫅 🤴 👸",
        "👳 👲 🧕 🤵 👰 🤰 🫃 🫄 🤱 👩‍🍼 👨‍🍼 🧑‍🍼 👼 🎅 🤶 🧑‍🎄",
        "🦸 🦹 🧙 🧚 🧛 🧜 🧝 🧞 🧟 🧌 💆 💇 🚶 🧍 🧎 🏃 💃 🕺 🕴️",
        "👯 🧖 🧗 🤸 🏌️ 🏇 🧘 🛀 🛌 🧑‍🤝‍🧑 👭 👫 👬 💏 💑 👪"
    ],
    Animals: [
        "🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐻‍❄️ 🐨 🐯 🦁 🐮 🐷 🐸 🐵 🙈 🙉 🙊",
        "🐒 🐔 🐧 🐦 🐤 🐣 🐥 🦆 🦅 🦉 🦇 🐺 🐗 🐴 🦄 🫎 🫏 🐝 🪱",
        "🐛 🦋 🐌 🐞 🐜 🪰 🪲 🪳 🦟 🦗 🕷️ 🕸️ 🦂 🐢 🐍 🦎 🦖 🦕",
        "🐙 🦑 🪼 🦐 🦞 🦀 🐡 🐠 🐟 🐬 🐳 🐋 🦈 🐊 🐅 🐆 🦓 🦍 🦧",
        "🦣 🐘 🦛 🦏 🐪 🐫 🦒 🦘 🦬 🐃 🐂 🐄 🐎 🐖 🐏 🐑 🦙 🐐 🦌",
        "🦮 🐕‍🦺 🐩 🐈 🐈‍⬛ 🪽 🪶 🐓 🦃 🦤 🦚 🦜 🦢 🪿 🦩 🕊️ 🐇 🦝",
        "🦨 🦡 🦫 🦦 🦥 🐁 🐀 🐿️ 🦔 🐾 🐉 🐲 🌵 🌲 🌳 🌴 🌱 🌿 ☘️"
    ],
    Nature: [
        "🍀 🍃 🍂 🍁 🍄 🪾 🌾 💐 🌷 🪷 🌹 🥀 🌺 🌸 🌼 🌻 🌞 🌝 🌛 🌜",
        "🌚 🌕 🌖 🌗 🌘 🌑 🌒 🌓 🌔 🌙 🌎 🌍 🌏 🪐 💫 ⭐ 🌟 ✨ ⚡ ☄️",
        "💥 🔥 🌪️ 🌈 ☀️ 🌤️ ⛅ 🌥️ ☁️ 🌦️ 🌧️ ⛈️ 🌩️ 🌨️ ❄️ ☃️ ⛄ 🌬️",
        "💧 💦 ☔ ☂️ 🌊 🫧"
    ],
    Food: [
        "🍏 🍎 🍐 🍊 🍋 🍋‍🟩 🍌 🍉 🍇 🍓 🫐 🍈 🍒 🍑 🥭 🍍 🥥 🥝 🍅",
        "🍆 🥑 🥦 🥬 🥒 🌶️ 🫑 🌽 🥕 🫒 🧄 🧅 🥔 🍠 🫚 🫘 🥜 🌰",
        "🍞 🥐 🥖 🫓 🥨 🥯 🥞 🧇 🧀 🍖 🍗 🥩 🥓 🍔 🍟 🍕 🌭 🥪 🌮 🌯",
        "🫔 🥙 🧆 🥚 🍳 🥘 🍲 🫕 🥣 🥗 🍿 🧈 🧂 🥫 🍱 🍘 🍙 🍚 🍛 🍜",
        "🍝 🍠 🍢 🍣 🍤 🍥 🥮 🍡 🥟 🥠 🥡 🦪 🍦 🍧 🍨 🍩 🍪 🎂 🍰 🧁",
        "🍫 🍬 🍭 🍮 🍯 🍼 🥛 ☕ 🫖 🍵 🧃 🥤 🧋 🍶 🍺 🍻 🥂 🍷 🥃 🧉",
        "🍸 🍹 🍾 🧊"
    ],
    Activities: [
        "⚽ ⚾ 🥎 🏀 🏐 🏈 🏉 🎾 🥏 🎳 🏏 🏑 🏒 🥍 🏓 🏸 🥊 🥋",
        "🥅 ⛳ 🪁 🏹 🎣 🤿 🥇 🥈 🥉 🏆 🏅 🎖️ 🏵️ 🎗️ 🎫 🎟️ 🎪 🤹",
        "🎭 🩰 🎨 🎬 🎤 🎧 🎼 🎹 🥁 🪘 🎷 🎺 🪗 🎸 🪕 🎻 🪇 🪈 🎲",
        "♟️ 🎯 🎮 🎰 🧩 🪩 🪅 🪆"
    ],
    Travel: [
        "🚗 🚕 🚙 🚌 🚎 🏎️ 🚓 🚑 🚒 🚐 🛻 🚚 🚛 🚜 🦯 🦽 🦼 🛴 🚲",
        "🛵 🏍️ 🛺 🚨 🚔 🚍 🚘 🚖 🛞 🚡 🚠 🚟 🚃 🚋 🚞 🚝 🚄 🚅 🚈 🚂",
        "🚆 🚇 🚊 🚉 ✈️ 🛫 🛬 🛩️ 💺 🛰️ 🚀 🛸 🚁 🛶 ⛵ 🚤 🛥️ 🛳️ ⛴️",
        "🚢 ⚓ 🛟 ⛽ 🚧 🚦 🚥 🗺️ 🗿 🗽 🗼 🏰 🏯 🏟️ 🎡 🎢 🎠 ⛲",
        "🏖️ 🏝️ 🏜️ 🌋 ⛰️ 🏔️ 🗻 🏕️ ⛺ 🛖 🏠 🏡 🏘️ 🏚️ 🏗️ 🏭 🏢 🏬",
        "🏣 🏤 🏥 🏦 🏨 🏪 🏫 🏩 💒 🏛️ ⛪ 🕌 🛕 🕍 ⛩️ 🕋"
    ],
    Objects: [
        "⌚ 📱 📲 💻 ⌨️ 🖥️ 🖨️ 🖱️ 🖲️ 💽 💾 💿 📀 🎥 🎞️ 📽️ 📺 📷 📸",
        "📹 📼 🔍 🔎 🕯️ 💡 🔦 🏮 🪔 📔 📕 📖 📗 📘 📙 📚 📓 📒 📃",
        "📜 📄 📰 🗞️ 📑 🔖 🏷️ 💰 🪙 💴 💵 💶 💷 💸 💳 🧾 💹 ✉️ 📧",
        "📨 📩 📤 📥 📦 📫 📪 📬 📭 📮 🗳️ ✏️ ✒️ 🖋️ 🖊️ 🖌️ 🖍️ 📝",
        "💼 📁 📂 🗂️ 📅 📆 🗒️ 🗓️ 📇 📈 📉 📊 📋 📌 📍 📎 🖇️ 📏 📐",
        "🔒 🔓 🔏 🔐 🔑 🗝️ 🔨 🪓 ⛏️ ⚒️ 🛠️ 🗡️ ⚔️ 🔫 🪃 🏹 🛡️ 🔧",
        "🪛 🔩 ⚙️ 🗜️ ⚖️ 🦯 🔗 ⛓️ 🪝 🧰 🧲 🪜 🧪 🧫 🧬 🔬 🔭 📡",
        "💉 🩸 💊 🩹 🩼 🩺 🩻 🚪 🛗 🪞 🪟 🛏️ 🛋️ 🪑 🚽 🪠 🚿 🛁",
        "🪤 🪒 🧴 🧷 🧹 🧺 🧻 🪣 🧼 🫧 🪥 🧽 🧯 🛒 🚬 ⚰️ 🪦 ⚱️",
        "🧿 🪬 🪧 🪪"
    ],
    Symbols: [
        "❤️ 🧡 💛 💚 💙 🩵 💜 🤎 🖤 🩶 🤍 💔 ❤️‍🔥 ❤️‍🩹 ❣️ 💕 💞 💓",
        "💗 💖 💘 💝 💟 ☮️ ✝️ ☪️ 🕉️ ☸️ ✡️ 🔯 🕎 ☯️ ☦️ 🛐 ⛎ ♈ ♉",
        "♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓ 🆔 ⚛️ 🉑 ☢️ ☣️ 📴 📳 🈶 🈚 🈸",
        "🈺 🈷️ ✴️ 🆚 💮 🉐 ㊙️ ㊗️ 🈴 🈵 🈹 🈲 🅰️ 🅱️ 🆎 🅾️ 🆑",
        "🅿️ 🆘 ❌ ⭕ 🛑 🚫 ⛔ 📛 🚷 🚯 🚳 🚱 🔞 📵 🚭 ❗ ❕ ❓ ❔",
        "‼️ ⁉️ 💯 🔅 🔆 🔱 ⚜️ 🔰 ♻️ ✅ ☑️ ✔️ ❎ ➰ ➿ 〽️ ✳️ ✴️",
        "❇️ ©️ ®️ ™️ #️⃣ *️⃣ 0️⃣ 1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣",
        "🔟 🔠 🔡 🔢 🔣 🔤 🅰️ 🆕 🆓 🆙 🆒 🆗 🆖 🆗 🆙 🔴 🟠 🟡 🟢",
        "🔵 🟣 🟤 ⚫ ⚪ 🟥 🟧 🟨 🟩 🟦 🟪 🟫 ⬛ ⬜ ◼️ ◻️ 🔶 🔷 🔸 🔹",
        "🔺 🔻 💠 🔘 🔳 🔲 ⭐ 🌟 ✨ 💫 🎉 🎊 🎈 🎁 🏳️ 🏴 🏁 🚩 🏳️‍🌈 🏳️‍⚧️"
    ]
};

function setupEmojiPicker(picker) {
    const search = picker.querySelector(".emoji-search");
    const categories = picker.querySelector(".emoji-categories");
    const grid = picker.querySelector(".emoji-grid");
    const form = picker.querySelector(".emoji-reaction-form");
    const input = form.querySelector('input[name="emoji"]');
    let activeCategory = "Smileys";

    function render() {
        const query = search.value.trim();
        const groups = query
            ? Object.entries(emojiCategories)
            : [[activeCategory, emojiCategories[activeCategory]]];

        grid.replaceChildren();
        for (const [category, rows] of groups) {
            const heading = document.createElement("h3");
            heading.className = "emoji-category-heading";
            heading.textContent = category;
            grid.append(heading);

            const group = document.createElement("div");
            group.className = "emoji-category-grid";
            for (const row of rows) {
                for (const emoji of row.split(" ")) {
                    if (query && !emoji.includes(query)) continue;
                    const button = document.createElement("button");
                    button.type = "button";
                    button.className = "emoji-option";
                    button.textContent = emoji;
                    button.setAttribute("aria-label", `React with ${emoji}`);
                    button.addEventListener("click", () => {
                        input.value = emoji;
                        picker.open = false;
                        form.requestSubmit();
                    });
                    group.append(button);
                }
            }
            grid.append(group);
        }
    }

    for (const category of Object.keys(emojiCategories)) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "emoji-category";
        button.textContent = category;
        button.setAttribute("aria-pressed", String(category === activeCategory));
        button.addEventListener("click", () => {
            activeCategory = category;
            search.value = "";
            for (const categoryButton of categories.children) {
                categoryButton.setAttribute(
                    "aria-pressed",
                    String(categoryButton === button)
                );
            }
            render();
        });
        categories.append(button);
    }

    search.addEventListener("input", render);
    render();
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".emoji-picker").forEach(setupEmojiPicker);
});
