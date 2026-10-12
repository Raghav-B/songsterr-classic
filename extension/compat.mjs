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
    return state;
}
