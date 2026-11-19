// Only restore UI data removed from October's server bootstrap. Never change
// user/profile, entitlement, payment, restrictions or experiment assignments.
export function adaptState(state) {
    if (!state.artist) {
        // October merged artist search into state.songs. July still owns an
        // independent artist result cache: copying the outer search state puts
        // its list one level too deep and crashes the header during navigation.
        const filters = state.songs.filters;
        const defaultInstrument = state.songs.defaultInstrument;
        state.artist = {
            id: 0,
            pattern: "",
            defaultInstrument,
            filters: structuredClone(filters),
            artists: {},
            loading: null,
            songs: {
                id: 0,
                list: [],
                hasMore: true,
                pattern: "",
                defaultInstrument,
                filters: structuredClone(filters),
            },
        };
    }
    // Newer server bootstraps omit the mixer's solo/mute selections. July
    // reads their lengths while rendering the top bar, so a missing list
    // unmounts the whole app. Fill only absent lists; keep any real selection.
    for (const key of ["player", "playerDiffBefore", "playerDiffAfter"]) {
        const player = state[key];
        if (!player || typeof player !== "object") continue;
        for (const list of PLAYER_LISTS) {
            if (!Array.isArray(player[list])) player[list] = [];
        }
        if (player.type === undefined) player.type = "focus";
    }
    return state;
}

const PLAYER_LISTS = ["partsToPlay", "partsSolo", "partsMute", "partsToPlayPrev", "partsSoloPrev", "partsMutePrev"];
