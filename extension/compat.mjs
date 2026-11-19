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
    // November's bootstrap reduced the player to loading flags. July reads the
    // mixer, speed and metronome fields while rendering and while restoring
    // saved per-song settings, so a missing one unmounts the whole app. Fill
    // only absent fields with July's neutral defaults; keep any real value.
    for (const key of ["player", "playerDiffBefore", "playerDiffAfter"]) {
        const player = state[key];
        if (!player || typeof player !== "object") continue;
        for (const [field, value] of Object.entries(PLAYER_DEFAULTS)) {
            if (Array.isArray(value) ? !Array.isArray(player[field]) : player[field] === undefined) {
                player[field] = structuredClone(value);
            }
        }
    }
    return state;
}

const PLAYER_DEFAULTS = {
    partsToPlay: [], partsSolo: [], partsMute: [],
    partsToPlayPrev: [], partsSoloPrev: [], partsMutePrev: [],
    type: "focus", speed: 100, soundVolume: 100, muteSound: false,
    pitchShift: 0, transposeNotation: 0,
    isMetronome: false, metronomeType: "regular", metronomeVolume: 100,
    isCountin: false, isCountinBetweenLoops: false,
    videoOpened: false, userAudioSelected: false, separatedAudioSelected: false,
};
