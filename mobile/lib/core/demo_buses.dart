import 'models/bus_model.dart';

/// Sample bus search results when the API is unreachable (UI testing only).
class DemoBuses {
  DemoBuses._();

  static List<BusSearchResult> forRoute({
    required String fromStop,
    required String toStop,
  }) {
    return [
      BusSearchResult(
        busId: 'demo-bus-1',
        busNumber: 'HR-29-1001',
        busType: 'express',
        status: 'running',
        delayMinutes: 0,
        etaDisplay: 'On time',
        currentStop: 'Zirakpur',
        nextStop: fromStop,
        routeNumber: 'HR-01',
        routeName: 'Chandigarh – Ambala Express',
        boardingStop: fromStop,
        destinationStop: toStop,
        fareInfo: const FareInfoModel(adultFareRupees: 41, distanceKm: 48),
        location: null,
        seatingCapacity: 52,
        standingCapacity: 20,
      ),
      BusSearchResult(
        busId: 'demo-bus-2',
        busNumber: 'HR-29-1002',
        busType: 'ordinary',
        status: 'running',
        delayMinutes: 10,
        etaDisplay: '10 min delay',
        currentStop: 'Rajpura',
        nextStop: fromStop,
        routeNumber: 'HR-02',
        routeName: 'Karnal – Ambala Ordinary',
        boardingStop: fromStop,
        destinationStop: toStop,
        fareInfo: const FareInfoModel(adultFareRupees: 35, distanceKm: 42),
        location: null,
        seatingCapacity: 52,
        standingCapacity: 20,
      ),
    ];
  }
}
