const init = () => {
    fetchNewSuggestions()
    document.querySelector("#get_suggestion_btn").addEventListener("click", fetchNewSuggestions)
    setInterval(updateStatus, 2500)
}

const setLoading = (loading) => {
    if (loading) {
        document.querySelector("#loading_icon").style.visibility = "visible"
    } else {
        document.querySelector("#loading_icon").style.visibility = "hidden"
    }
}

const updateStatus = () => {

    fetch("/status", {
            method: "GET"
        }).then(response => response.json())
        .then((response) => {
            const txt = response && response.queued > 0 ? `Queued: ${response.queued}` : ""
            document.querySelector("#queue").innerText = txt
        }).catch(error => console.log(error))
}

const generate = (quote, motive) => {
    fetch("/trigger?" + new URLSearchParams({
            quote,
            motive,
            channel_id: ""
        }), {
            method: "GET"
        }).then(() => {
            updateStatus()
        })
        .catch(error => console.log(error))
}

const fetchNewSuggestions = () => {
    fetch("/fetch-next?" + new URLSearchParams({
            num: 5
        }), {
            method: "GET"
        }).then(response => response.json()).then(response => {
            setLoading(false)

            response.forEach(([motive, quote]) => {
                const el = document.createElement("a")
                el.className = "list-group-item list-group-item-action"
                el.style.cursor = "pointer"
                el.innerHTML = `<strong>${quote}</strong> ${motive}`
                el.onclick = () => {
                    el.className = el.className + " disabled"
                    generate(quote, motive)
                }
                document.querySelector("#suggestions_list").prepend(el)
            })
        })
        .catch(error => {
            setLoading(false)
            console.error(error)
        })

    setLoading(true)
}


window.addEventListener("load", init)