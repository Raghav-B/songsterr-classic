// July already replays add/remove/move commands into track metadata. Use that
// result, not instrument names or array positions guessed from the final score.
globalThis.classicTrackIdentities = (tracks, partCount) => {
    if (!Array.isArray(tracks) || tracks.length !== partCount) {
        throw new Error("Classic cannot match this revision's tracks. No revision was sent.");
    }
    const identities = Array(partCount).fill(null);
    const seen = new Set();
    for (const track of tracks) {
        const position = track.partId;
        if (!Number.isInteger(position) || position < 0 || position >= partCount || seen.has(position)) {
            throw new Error("Classic found ambiguous track positions. No revision was sent.");
        }
        seen.add(position);
        identities[position] = track.hash || null;
    }
    return identities.some(identity => identity !== null) ? identities : undefined;
};
