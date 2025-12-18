import React from "react";
import "./clipboardCopy.css"

function ClipboardCopy({ copyText }) {

    async function copyTextToClipboard(text) {
        if ('clipboard' in navigator) {
            return await navigator.clipboard.writeText(text);
        } else {
            return document.execCommand('copy', true, text);
        }
    }

    // onClick handler function for the copy button
    const handleCopyClick = () => {
        // Asynchronously call copyTextToClipboard
        copyTextToClipboard(copyText)
    }

    return (
        <div>
            <input className="clipcopy__input" type="text" value={copyText} readOnly />
            {/* Bind our handler function to the onClick button property */}
            <button onClick={handleCopyClick}>
                <span>{'Copy'}</span>
            </button>
        </div>
    );
}

export default (ClipboardCopy)