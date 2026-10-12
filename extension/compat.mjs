// Only restore UI data removed from October's server bootstrap. Never change
// user/profile, entitlement, payment, restrictions or experiment assignments.
export function adaptState(state) {
    if (!state.artist) {
        state.artist = {
            pattern: "",
            filters: structuredClone(state.songs.filters),
            artists: {},
            songs: structuredClone(state.songs),
        };
    }
    return state;
}
