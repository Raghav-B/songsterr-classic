# Release preparation

Chrome ships as an unpacked-extension ZIP. The current Firefox XPI is unsigned
and supports temporary loading only. Signing is on hold: do not submit to
Mozilla without the repository owner's request. Keep this limitation explicit
in the README and release notes. Do not label an unsigned build as persistently
installable.

## Prepare

Build both packages using [development](development.md). Run the archive tests
and Mozilla's validator against the generated Firefox directory:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
npx --yes web-ext@10.7.0 lint --source-dir artifacts/firefox-extension
```

Keep the complete lint output for reviewers. Warnings are not approval and
must not be silently filtered out. Select desktop platforms for this release;
Android has not been tested.

## Optional future Firefox signing

If signing is requested, use Mozilla's unlisted distribution route. Unlisted
describes distribution, not a review exemption.

1. Sign in to the [Mozilla developer hub](https://addons.mozilla.org/developers/).
2. Submit a new add-on, choosing **On your own** (unlisted distribution).
3. Upload the generated Firefox XPI. Retain the stable Gecko ID from the build.
4. Supply source/build instructions and reviewer notes explaining the archived
   frontend, compatibility patches, service requests and validator warnings.
5. Resolve validation or reviewer requests. Download the signed XPI when available.

Our wrapper source and build scripts are readable. The archived Songsterr
frontend is minified; we do not have its original unminified source. Include
that fact in reviewer notes. A reproducible archive of those vendor files does
not replace their original source or guarantee acceptance.

Keep signing credentials out of the repository, release assets and chat. Never
modify or re-zip the XPI after Mozilla signs it. Every updated Firefox package
needs its own signature; uploading an XPI to GitHub does not sign it.

## Verify a signed build

- Install the signed XPI through **Install Add-on From File** in a fresh standard
  Firefox profile with default signature enforcement. Restart that test browser
  and verify the extension is still installed, its popup works, and Classic
  activates. Leave unrelated browser sessions untouched.
- Replace the draft's unsigned Firefox asset with the verified signed XPI.
- Generate SHA256SUMS from the exact downloadable files after signing.
- Keep Chrome ZIP, Firefox XPI and source ZIP at the same extension version.
- Update README and release notes from signing-pending to signed only after
  verification. Keep unsigned temporary-loading instructions in development docs.

## Stage either package type

- For an unsigned Firefox build, retain the README's temporary-loading steps
  and state that **Install Add-on From File** does not work in regular Firefox.
- Generate SHA256SUMS from the exact downloadable Chrome ZIP, Firefox XPI and
  source ZIP, and verify the uploaded assets against those hashes.
- Confirm the release is still a draft and repository visibility is unchanged.
  Public publication remains the repository owner's final action/approval.

No Firefox update URL is currently configured. Users install newer signed XPI
files manually. Chrome users keep their extracted folder and reload the extension
when they replace its files.
