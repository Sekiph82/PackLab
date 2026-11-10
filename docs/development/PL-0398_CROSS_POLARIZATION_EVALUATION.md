# PL-0398 — Cross-polarized lighting for glossy packaging

## Recommendation

Keep cross-polarization as an **optional, paired evaluation mode** for glossy opaque packages. Do not make it the default scan-station lighting recipe until a controlled trial demonstrates that it improves the actual reconstruction and dimensional checks on PackLab-relevant plastics. Published work supports suppressing some specular reflections and improving image matching, but outcomes depend on material, surface finish, lighting/view geometry, and the reconstruction workflow. Results on heritage objects or other reflective surfaces are evidence for testing the method, not proof for HDPE, PET, or PP packages.

## What the method changes

Place linear polarizing film over each diffuse light source with their transmission axes aligned. Fit a rotatable linear analyzer to the camera lens. With the lights on, rotate the analyzer toward the crossed position (nominally 90° relative to the source filters) while observing the reflected highlight. Preserve a parallel/co-polarized or ordinary diffuse-light reference set as well. The nominal 90° is a starting orientation; record the measured mark/angle and actual lighting arrangement because real filters, curved surfaces, and multiple reflection paths can leave residual glare.

Cross-polarization rejects part of the polarization-preserving surface reflection and can make some diffuse surface detail more consistent across views. It also reduces received light. It cannot create texture or geometric signal that the package does not provide. On smooth, low-texture packaging, stronger highlight suppression can therefore make matching worse even if the images look less glossy. Curved shoulders, recessed details, labels, seams, and closures may respond differently within the same package.

## Evidence and limitations

Conen et al. describe polarizers on both camera and light sources and report that crossing their directions suppressed reflections, yielding more homogeneous images and improved matching in dense stereo; the work also includes accuracy assessment against laser triangulation. This is relevant evidence for evaluating the approach, but does not establish performance on packaging polymers.

A cross-polarized photogrammetry workflow documented for reflective heritage objects used polarized LED sources and a camera polarizer at a crossed orientation, and compared paired polarization states. The authors discuss material-dependent results and added acquisition/processing effort. Clini et al. report cross-polarization in combination with pattern projection and HDR for a shiny, textureless ceramic surface. That combined method must not be represented as evidence that cross-polarization alone solves textureless package reconstruction.

Clear and translucent PET are separate optical cases. Cross-polarization may change surface glare, but transmitted light, refraction, internal reflections, and stress birefringence remain; the method is not a substitute for a validated way to observe the container boundary. This is an optical/workflow limitation inferred from the nature of transparent plastic and the cited literature, not a PackLab capture result.

## Proposed controlled trial (not yet performed)

When the station and representative physical samples exist, compare separate image sets of the same stationary package using:

1. baseline matched diffuse lights without polarizers;
2. parallel/co-polarized lights and lens analyzer, if practical; and
3. crossed light polarizers and lens analyzer.

Keep camera/lens, camera and object poses, viewpoint list, lighting positions/output, focus, aperture, shutter, ISO, white balance, background, and image processing fixed or recorded. Because crossed filters reduce light, set exposure safely before the trial and keep it fixed across each comparison; record any unavoidable exposure change as a confound. Capture the same viewpoints in each set. Process each lighting condition separately through the same reconstruction settings; do not combine polarization pairs at identical viewpoints into an ordinary SfM input set unless a dedicated experiment validates that choice.

Include at least one glossy opaque package (for example, molded HDPE or glossy PP) and a separately reported clear or translucent PET container. Preserve unmodified source images and record material identification as known/unknown rather than inferred from appearance. Compare:

- usable tie-point count and fraction of registered views;
- reprojection residual distribution and rejected/outlier observations;
- reconstructed surface coverage and obvious missing/duplicated geometry;
- scale-reference residual and dimensional error against independently measured dimensions with tool identity and calibration/verification status; and
- texture/label readability and highlight artifacts as separate visual outcomes.

Choose acceptance thresholds before collecting physical data, based on the intended PackLab use and measurement-tool uncertainty. A lower reprojection residual alone is not proof of more accurate dimensions. Keep any treatment, spray, powder, coating, or label removal outside this task; PL-0399 addresses whether removable treatments are safe and acceptable.

## Current PackLab status

This document is a source-based recommendation and a proposed future experiment only. No PackLab station, physical package, polarization filter, real capture, reconstruction comparison, dimensional measurement, Kenya facility, or local production process was available or tested for PL-0398. No performance conclusion or physical acceptance is claimed.

## References

- N. Conen, H. Hastedt, O. Kahmen, T. Luhmann, [“Improving image matching by reducing surface reflections using polarising filter techniques”](https://isprs-archives.copernicus.org/articles/XLII-2/267/2018/), ISPRS Archives (2018). DOI: 10.5194/isprs-archives-xlii-2-267-2018.
- A. Frost et al., [“Digital Documentation of Reflective Objects: A Cross-Polarised Photogrammetry Workflow for Complex Materials”](https://link.springer.com/chapter/10.1007/978-3-031-35593-6_7), Springer (2023). Heritage-object workflow; qualitative/material-specific findings and acquisition trade-offs.
- P. Clini et al., [“Combining pattern projection and cross polarization to enhance 3D reconstruction of featureless reflective surfaces”](https://isprs-archives.copernicus.org/articles/XLVIII-M-2-2023/427/2023/), ISPRS Archives (2023), licensed CC BY 4.0. The reported workflow combines noise-function pattern projection and cross-polarization; it is not a cross-polarization-only result.
