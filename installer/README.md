# Voicy download installer

A small Apple Silicon macOS 14+ app downloads the complete Voicy 0.3.3 offline disk image from four GitHub release payload assets. It streams to a private temporary directory on the selected disk, checks each part and the whole image with SHA-256, adds Internet-download quarantine and reveals the verified disk image in Finder. The user opens that image and drags Voicy to Applications. It never uploads recordings and needs no account. Initial setup requires the network and about 6.5 GB of downloads; the installed speech models run locally.

This is a distribution fallback for the unavailable object-storage publishing credential. It avoids putting a production download behind an expiring development tunnel, a browser CORS proxy or manual multipart assembly. It does not change Voicy's speech engine, model settings or model licenses.

`payload.json` is generated from the exact qualified final DMG and its four public payload files. It is sealed in the signed app; no remote manifest or executable script is fetched. Do not build or publish from placeholder hashes or an unqualified image. The existing internal validation drafts remain unpublished and are not consumer downloads.

```sh
installer/build.sh /absolute/path/to/qualified-payload.json /absolute/path/to/new-output-directory
```

The build refuses to replace an existing app. Sign and notarize the app and its small distribution DMG with the existing owner identity, then test the actual signed download and completed offline app installation. Publish the consumer installer and its exact payload assets together in the proper `v0.3.3` release. Do not claim those publication/native-flow gates passed merely because the source checks below pass.

Focused tests run on standard macOS 14/15 hosts. They use URLProtocol fixtures, real streaming file writes, CryptoKit and quarantine properties to check complete bytes, per-part/whole hash failure, truncation, HTTP errors, cancellation, destination collisions and preservation of existing files. These are separate from actual public download, Gatekeeper and Voicy native import/enhancement/export qualification.

Staging uses Apple's [item replacement directory](https://developer.apple.com/documentation/foundation/filemanager/url%28for%3Ain%3Aappropriatefor%3Acreate%3A%29) on the target volume. Publication and cleanup use the held directory descriptor; the verified file remains open until exclusive publication. The assistant reveals the saved file in Finder and does not execute downloaded content.
